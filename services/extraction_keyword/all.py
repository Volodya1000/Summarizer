from pydantic import BaseModel, Field
from typing import List, Tuple, Set, Dict
import re
import nltk
import yake
import argostranslate.translate
import argostranslate.package
import argostranslate.translate
from models import KeywordNode, KeywordTreeSummary
# Проверка и установка пакета RU→EN
import logging
import pathlib
import argostranslate.package
import argostranslate.translate
import asyncio
from langdetect import detect

def ensure_argos_pair(src: str, tgt: str) -> bool:
    """Проверка наличия установленной пары src→tgt."""
    try:
        langs = argostranslate.translate.get_installed_languages()
        from_lang = next((l for l in langs if l.code == src), None)
        to_lang = next((l for l in langs if l.code == tgt), None)
        if from_lang and to_lang and from_lang.get_translation(to_lang):
            return True
    except Exception:
        return False

    try:
        argostranslate.package.update_package_index()
        avail = argostranslate.package.get_available_packages()
        pkg = next((p for p in avail if p.from_code == src and p.to_code == tgt), None)
        if not pkg:
            return False
        pkg_path = pkg.download()  # AvailablePackage.download() -> pathlib.Path
        argostranslate.package.install_from_path(pkg_path)
        return True
    except Exception:
        return False


    # проверим ещё раз
    installed_langs = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed_langs if l.code == src), None)
    to_lang = next((l for l in installed_langs if l.code == tgt), None)
    try:
        ok = from_lang is not None and to_lang is not None and from_lang.get_translation(to_lang) is not None
        logger.info("Пара %s→%s установлена: %s", src, tgt, ok)
        return ok
    except Exception:
        return False

ensure_argos_pair("en", "ru")
ensure_argos_pair("ru", "en")


class LocalTranslator:
    """Локальный переводчик: использует high-level API argostranslate.translate.translate,
    и в качестве fallback — внутренний объект перевода (если есть), иначе возвращает исходник.
    """
    def __init__(self):
        pass

    def translate(self, phrase: str, src: str, tgt: str) -> str:
       return argostranslate.translate.translate(phrase, src, tgt)
    
# ----------------------------
# Настройки
# ----------------------------
YAKE_TOP_K = 40
MERGE_THRESH = 0.3
SOFT_JACCARD_ATTACH = 0.18
MIN_CORE_NOUNS = 1




# ----------------------------
# Стоп-слова
# ----------------------------

from nltk.corpus import stopwords
nltk.download('stopwords', quiet=True)
STOP_WORDS_RU = set(stopwords.words('russian'))
STOP_WORDS_EN = set(stopwords.words('english'))

# ----------------------------
# Лемматизация / токенизация
# ----------------------------
USE_SPACY = False
USE_PYMORPHY = False
nlp_ru = nlp_en = None
morph = None

if not USE_SPACY:
    try:
        import pymorphy2
        morph = pymorphy2.MorphAnalyzer()
        USE_PYMORPHY = True
    except Exception:
        USE_PYMORPHY = False

def normalize_text(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^\w\s\-]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def spacy_core_tokens(phrase: str, lang: str) -> Tuple[List[str], List[str]]:
    doc = nlp_ru(phrase) if lang=="ru" else nlp_en(phrase)
    lemmas, poses = [], []
    for token in doc:
        if token.is_stop or token.is_punct or not token.lemma_:
            continue
        lem = token.lemma_.strip().lower()
        pos = token.pos_
        if lem and lem not in lemmas:
            lemmas.append(lem)
            poses.append(pos)
    return lemmas, poses

def pymorphy_core_tokens(phrase: str) -> Tuple[List[str], List[str]]:
    toks, poses = [], []
    for w in normalize_text(phrase).split():
        if w in STOP_WORDS_RU:
            continue
        parsed = morph.parse(w)
        if not parsed:
            continue
        p = parsed[0]
        toks.append(p.normal_form)
        poses.append(p.tag.POS or "X")
    return toks, poses

def simple_core_tokens(phrase: str, lang: str) -> Tuple[List[str], List[str]]:
    toks, poses = [], []
    stop_words = STOP_WORDS_RU if lang=="ru" else STOP_WORDS_EN
    for w in normalize_text(phrase).split():
        if w in stop_words:
            continue
        if w not in toks:
            toks.append(w)
            poses.append("X")
    return toks, poses

def core_tokens_with_pos(phrase: str, lang: str) -> Tuple[List[str], List[str]]:
    if USE_SPACY:
        return spacy_core_tokens(phrase, lang)
    if USE_PYMORPHY and lang=="ru":
        return pymorphy_core_tokens(phrase)
    return simple_core_tokens(phrase, lang)

# ----------------------------
# Метрики
# ----------------------------
def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = a.intersection(b)
    uni = a.union(b)
    return len(inter)/len(uni) if uni else 0.0

# ----------------------------
# YAKE извлечение
# ----------------------------
def extract_key_phrases(text: str, lang: str, top_k: int=YAKE_TOP_K) -> List[str]:
    kw_extractor = yake.KeywordExtractor(lan=lang, n=4, top=top_k, dedupLim=0.9)
    kws = kw_extractor.extract_keywords(text)
    return [kw[0] for kw in kws]

# ----------------------------
# Кластеризация
# ----------------------------
def cluster_phrases(phrases: List[str], merge_thresh: float=MERGE_THRESH, lang: str="ru") -> List[Dict]:
    items = []
    for i, p in enumerate(phrases):
        lemmas, poses = core_tokens_with_pos(p, lang)
        core_set = set(lemmas)
        items.append({
            "members": {i},
            "phrases": [p],
            "core_list": lemmas,
            "core_pos": poses,
            "core_set": core_set
        })

    def best_pair(items_list):
        best = (None, None, -1.0)
        n = len(items_list)
        for i in range(n):
            for j in range(i+1,n):
                score = jaccard(items_list[i]["core_set"], items_list[j]["core_set"])
                if score > best[2]:
                    best = (i,j,score)
        return best

    items_list = items.copy()
    while True:
        i,j,score = best_pair(items_list)
        if score < merge_thresh or i is None:
            break
        A,B = items_list[i], items_list[j]
        new_members = A["members"]|B["members"]
        new_phrases = A["phrases"]+B["phrases"]
        inter = list(A["core_set"].intersection(B["core_set"]))
        if inter:
            combined=[]
            for token in A["core_list"]+B["core_list"]:
                if token in inter and token not in combined:
                    combined.append(token)
            new_core_list=combined
            new_core_set=set(new_core_list)
            new_core_pos=[]
            for t in new_core_list:
                pos=None
                if t in A["core_list"]:
                    pos=A["core_pos"][A["core_list"].index(t)]
                elif t in B["core_list"]:
                    pos=B["core_pos"][B["core_list"].index(t)]
                new_core_pos.append(pos or "X")
        else:
            union_tokens = list(A["core_list"]+B["core_list"])
            freq = {}
            for t in union_tokens:
                freq[t]=freq.get(t,0)+1
            sorted_by_freq = sorted(freq.keys(), key=lambda x:(-freq[x], union_tokens.index(x)))
            new_core_list = sorted_by_freq[:3]
            new_core_set = set(new_core_list)
            new_core_pos=[]
            for t in new_core_list:
                pos=None
                if t in A["core_list"]:
                    pos=A["core_pos"][A["core_list"].index(t)]
                elif t in B["core_list"]:
                    pos=B["core_pos"][B["core_list"].index(t)]
                new_core_pos.append(pos or "X")

        new_item={"members":new_members,"phrases":new_phrases,
                  "core_list":new_core_list,"core_pos":new_core_pos,"core_set":new_core_set}
        items_list=[it for k,it in enumerate(items_list) if k not in (i,j)]
        items_list.append(new_item)
    clusters=[]
    for it in items_list:
        core_list=it["core_list"]
        core_set=it["core_set"]
        core_pos=it.get("core_pos",[])
        phrases_in_cluster=it["phrases"]
        if not core_list:
            tokens=[]
            for p in phrases_in_cluster:
                for w in normalize_text(p).split():
                    stop_words = STOP_WORDS_RU if lang=="ru" else STOP_WORDS_EN
                    if w in stop_words:
                        continue
                    if w not in tokens:
                        tokens.append(w)
            core_list=tokens[:3]
            core_set=set(core_list)
            core_pos=["X"]*len(core_list)
        name=None
        for tok,pos in zip(core_list,core_pos):
            if pos and pos.upper().startswith(("NOUN","PROPN","N")):
                name=tok
                break
        if not name and core_list:
            name=core_list[0]
        if not name:
            name=min(phrases_in_cluster,key=lambda s: len(s))
        clusters.append({
            "name":name,
            "members":it["members"],
            "core_set":core_set,
            "core_list":core_list,
            "core_pos":core_pos,
            "phrases":phrases_in_cluster
        })
    return clusters

# ----------------------------
# Построение дерева
# ----------------------------
def build_tree_from_clusters(clusters: List[Dict], lang: str="ru") -> List[KeywordNode]:
    node_data=[]
    for c in clusters:
        core=c["core_set"]
        core_pos=c.get("core_pos",[])
        strong=any((pos and pos.upper().startswith(("NOUN","PROPN","N"))) for pos in core_pos)
        node=KeywordNode(name=c["name"])
        node_data.append({"name":c["name"],"core_set":core,"core_list":c["core_list"],
                          "core_pos":core_pos,"phrases":c["phrases"],"node":node,
                          "size":len(core),"strong":strong})
    node_data.sort(key=lambda x:(x["size"],not x["strong"],x["name"]))
    n=len(node_data)
    is_child=set()
    for i,parent in enumerate(node_data):
        for j,child in enumerate(node_data):
            if i==j:
                continue
            if parent["core_set"] and parent["core_set"].issubset(child["core_set"]) and parent["core_set"]!=child["core_set"]:
                parent["node"].children.append(child["node"])
                is_child.add(j)
    for i,parent in enumerate(node_data):
        if parent["size"]==1 and parent["strong"]:
            token=next(iter(parent["core_set"]))
            for j,child in enumerate(node_data):
                if i==j or j in is_child:
                    continue
                found_in_phrase=any(token in normalize_text(p) for p in child["phrases"])
                if found_in_phrase and j not in is_child:
                    parent["node"].children.append(child["node"])
                    is_child.add(j)
    for i,parent in enumerate(node_data):
        for j,child in enumerate(node_data):
            if i==j or j in is_child:
                continue
            if parent["core_set"] and child["core_set"]:
                score=jaccard(parent["core_set"],child["core_set"])
                if score>=SOFT_JACCARD_ATTACH and parent["size"]<child["size"]:
                    parent["node"].children.append(child["node"])
                    is_child.add(j)
    roots=[nd["node"] for idx,nd in enumerate(node_data) if idx not in is_child]
    final_roots=[]
    for r in roots:
        nd=next((x for x in node_data if x["node"] is r), None)
        if nd and not nd["strong"]:
            best_score=0.0
            best_idx=None
            for k,cand in enumerate(node_data):
                if cand is nd:
                    continue
                if cand["strong"]:
                    s=jaccard(nd["core_set"],cand["core_set"])
                    if s>best_score:
                        best_score=s
                        best_idx=k
            if best_idx is not None and best_score>0:
                cand_node=node_data[best_idx]["node"]
                for ph in nd["phrases"]:
                    if ph not in {c.name for c in cand_node.children}:
                        cand_node.children.append(KeywordNode(name=ph))
                continue
        final_roots.append(r)
    if not final_roots:
        final_roots=roots
    for nd in node_data:
        cluster_core=nd["core_set"]
        for phrase in nd["phrases"]:
            phrase_core,_=core_tokens_with_pos(phrase, lang)
            phrase_core_set=set(phrase_core)
            if phrase_core_set and cluster_core and cluster_core.issubset(phrase_core_set) and phrase_core_set!=cluster_core:
                existing={c.name for c in nd["node"].children}
                if phrase not in existing:
                    nd["node"].children.append(KeywordNode(name=phrase))
    return final_roots
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ExtractionKeywordService:
    """
    Асинхронный сервис для извлечения ключевых слов и построения двуязычного дерева.
    Всегда возвращает KeywordTreeSummary (RU и EN) независимо от исходного языка.
    """
    def __init__(self, translator: LocalTranslator):
        # Удаляем self.lang, так как он определяется динамически
        self.translator = translator

    def detect_language(self,text: str) -> str:
        try:
            lang = detect(text)
            if lang.startswith("ru"):
                return "ru"
            return "en"
        except Exception:
            return "en"


    async def _translate_tree(self, nodes: List[KeywordNode], src: str, tgt: str) -> List[KeywordNode]:
        """
        Асинхронно рекурсивно переводит имена узлов в дереве. 
        """
        translated_nodes = []
        for node in nodes:
            name_translated = self.translator.translate(node.name, src=src, tgt=tgt)
            
            translated_children = await self._translate_tree(node.children, src=src, tgt=tgt)
            # Предполагаем, что конструктор KeywordNode принимает 'name' и 'children'
            translated_nodes.append(KeywordNode(name=name_translated, children=translated_children))
            
        return translated_nodes

    async def generate(self, text: str) -> KeywordTreeSummary:
        """
        Основной асинхронный метод для построения двуязычного дерева.
        Входной параметр 'lang' удален. Язык определяется автоматически.
        
        :param text: Исходный текст.
        :return: Объект KeywordTreeSummary с деревьями на RU и EN.
        """
        
        # ШАГ 0: АВТОМАТИЧЕСКОЕ ОПРЕДЕЛЕНИЕ ЯЗЫКА
        source_lang = self.detect_language(text)
        logger.info("Detected language: %s", source_lang)

        phrases = extract_key_phrases(text, lang=source_lang)
        logger.info("Extracted phrases: %s", phrases)

        clusters = cluster_phrases(phrases, lang=source_lang)
        logger.info("Clusters: %s", [c["name"] for c in clusters])

        roots_original = build_tree_from_clusters(clusters, lang=source_lang)
        logger.info("Root nodes: %s", [r.name for r in roots_original])

        
        # Шаг 3: Перевод дерева
        target_lang = "en" if source_lang == "ru" else "ru"
        roots_translated = await self._translate_tree(roots_original, src=source_lang, tgt=target_lang)
        
        # Шаг 4: Формирование результата (берем только первый корневой узел)
        # Если не найдено ключевых слов, создаем заглушку
        default_node = KeywordNode(name="No keywords found", children=[])
        
        if source_lang == "ru":
            ru_tree = roots_original if roots_original else [default_node]
            en_tree = roots_translated if roots_translated else [default_node]
        else:
            en_tree = roots_original if roots_original else [default_node]
            ru_tree = roots_translated if roots_translated else [default_node]


        result = KeywordTreeSummary(ru=ru_tree, en=en_tree)

        logger.info(result.model_dump_json(indent=2))

        return KeywordTreeSummary(ru=ru_tree, en=en_tree)