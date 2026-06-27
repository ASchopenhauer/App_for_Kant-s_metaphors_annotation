import streamlit as st
# import streamlit_shadcn_ui as ui
import uuid # 2026-06-11
import json
import pickle
import os
from collections import defaultdict

import requests
from deep_translator import GoogleTranslator # 2026-05-29 (14h20) : On verra si c’est une bonne idée

def toggle_token_filter_lexical():
    st.session_state.token_filter_lexical = not st.session_state.token_filter_lexical

def select_options(token, i, key, message):

    token[key] = st.selectbox(
        message,
        ["null", "true", "false"],
        index=0 if token.get(key) is None else (1 if token[key] else 2),
        key=f"{key}_{i}_{st.session_state.data_id}"
    )

    if token[key] == "null":
        token[key] = None
    else:
        token[key] = token[key] == "true" # Est-ce bien nécessaire ? Mais oui ! Ça transforme le string en booléen !

def write_comment(token, i, key, message):

    token[key] = st.text_area(
        message,
        value=token.get(key, ""),
        key=f"{key}_{i}_{st.session_state.data_id}"
    )

    if token[key] == "":
        token[key] = None

def write_gold(token, i, key, message, long: bool = False):

    if long: # 2026-05-31 (17h07)
        token[key] = st.text_area(
            message,
            value=token.get(key, ""),
            key=f"{key}_{i}_{st.session_state.data_id}"
        )        

    else:
        token[key] = st.text_input(
            message,
            value=token.get(key, ""),
            key=f"{key}_{i}_{st.session_state.data_id}"
        )

    if token[key] == "":
        token[key] = None


def select_level_options(token, i, key, message, help): # 2026-05-29 (13h43)
    level_options = ["good", "bad", "partial"]
    token[key] = st.selectbox(
        message,
        ["null"] + level_options,
        index=0 if token.get(key) is None else (level_options.index(token[key]) + 1),
        key=f"{key}_{i}_{st.session_state.data_id}",
        help=help
    )

    if token[key] == "null":
        token[key] = None

def select_quality_options(token, i, key, message): # 2026-05-31 (03h29)
    level_options = ["good", "rather_good", "not_satisfying", "bad"]
    token[key] = st.selectbox(
        message,
        ["null"] + level_options,
        index=0 if token.get(key) is None else (level_options.index(token[key]) + 1),
        key=f"{key}_{i}_{st.session_state.data_id}",
        # help=help
    )

    if token[key] == "null":
        token[key] = None    

def select_undetected_cause_options(token, token_annotation, i): # 2026-06-27 (16h22)
    key = "undetected_cause"
    message = "Why is the token not detected?"
    level_options = ["lemmatisation", "themes_selection", "extraction_process_from_OCR", "not_in_Niemann", "not_in_lexical_resources"]

    default_cause = None
    if token_annotation["spacy_lemma_is_correct"] == False:
        default_cause = "lemmatisation"
    elif token["themes"] not in ["No entry found.", ""] and not token["selected_themes"]:
        default_cause = "themes_selection"
    elif token_annotation.get("ocr_check") and token_annotation["ocr_check"] == {}:
        default_cause = "not_in_Niemann"
    
    selected = token_annotation.get(key) if token_annotation.get(key) is not None else default_cause

    if selected in level_options:
        index = level_options.index(selected) + 1
    else:
        index = 0
    
    token_annotation[key] = st.selectbox(
        message,
        ["null"] + level_options,
        index=index,
        key=f"{key}_{i}_{st.session_state.data_id}",
        # help=help
    )

    if token_annotation[key] == "null":
        token[key] = None 

def write(text):
    st.markdown(
        f"<span style='font-size:16px; color:gray;'>{text}</span>",
        unsafe_allow_html=True
    )

def render_paragraph(data, show_non_candidates: bool): # TODO Voir si je l’intègre ensuite dans la fonction

    # 2026-05-30 (15h30)
    text = data["text"]
    candidate_tokens = [token for token in data["semantic_tokens"].values() if str(token["token_index"]) in data["candidate_tokens"]]

    html=""
    
    # Styles testés
    # style_focus = """
    #     background-color: #fff3b0;
    #     color: #333;
    #     padding: 0 4px;
    #     border-radius: 4px;
    # """
    # style_focus = """
    #     background-color:#ff4d4d;
    #     color:white;
    #     border-radius:4px;
    # """ 
    # style_focus = """
    #     background-color: #eef2ff;
    #     color: #4338ca;
    #     padding: 2px 8px;
    #     border-radius: 999px;
    #     font-weight: 600;
    # """
    # style_focus = """
    #     color: inherit;
    #     font-weight: 600;
    #     border-bottom: 3px solid #60a5fa;
    # """
    # style_focus = """
    #     color: #2563eb;
    #     font-weight: 600;
    # """

    # 2026-05-30 (12h32) : On va rester sur ce choix pour l’instant
    style_focus = """
        background-color: rgba(59, 130, 246, 0.12);
        color: #1e40af;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 500;
    """

    style_not_yet = """
        background-color: rgba(107, 114, 128, 0.08);
        color: #6b7280;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 400;    
    """

    markup_left_by_state = {
        "candidate": f'<span style="{style_focus}">',
        "not_candidate": f'<span style="{style_not_yet}">'
    }
    markup_right = '</span>'

    previous_end = 0

    for idx, token in data["semantic_tokens"].items():
        is_candidate = idx in data["candidate_tokens"]

        if not show_non_candidates and not is_candidate:
            continue

        state = "candidate" if is_candidate else "not_candidate"
        markup_left = markup_left_by_state[state]

        html += text[previous_end:token["start_char"]] + markup_left + token["text"] + markup_right
        previous_end = token["end_char"]
    html += text[previous_end:]

    return html


def render_sentence(token):
    html = ""
    sentence = token["sentence"]
    token_start_in_sentence = token["start_char"] - token["sentence_start_char"]
    style_focus = """
        background-color: rgba(59, 130, 246, 0.12);
        color: #1e40af;
        padding: 2px 6px;
        border-radius: 6px;
        font-weight: 500;
    """
    html = (
        f"{sentence[0:token_start_in_sentence]}"
        f'<span style="{style_focus}">{token["text"]}</span>'
        f"{sentence[token_start_in_sentence + len(token['text']):]}" # ⚠ Pas de virgules
        )
    
    return html

def render_syntactic_group(token):
    html = ""
    group = token["syntactic_group"]
    if group is None:
        return ""
    parts = group.split(token["text"])
    style_focus = """
        background-color:#ff4d4d;
        color:white;
        border-radius:4px;
    """ 
    html = (
        f"{parts[0]}"
        f'<span style="{style_focus}">{token["text"]}</span>'
        f"{parts[1]}"
    )

    return html

def translate_lemme(lemme): # 2026-05-29 (14h23)
    translation = GoogleTranslator(source="de", target="fr").translate(lemme)
    return translation.lower()

### Lexical search ###

def word_is_in_wiktionary_de(word: str) -> bool | None:
    """
    Check if a web page exists in the german wiktionary
    """
    url = "https://de.wiktionary.org/w/api.php"

    headers = {
        "User-Agent": "MyStreamlitLexiconApp/1.0 (contact: me@example.com)"
    }

    params = {
        "action": "query",
        "titles": word,
        "format": "json"
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()

    except requests.exceptions.RequestException as e:
        st.warning(f"Wiktionary is unavailable for “{word}”: {e}")
        return None

    except ValueError:
        st.warning(f"Wiktionary response invalid for “{word}”")
        return None

    pages = data["query"]["pages"]

    return not any("missing" in page for page in pages.values())

def word_is_in_dwds(word: str) -> bool | None:
    url = f"https://www.dwds.de/wb/{word}"

    try:
        r = requests.get(
            url,
            allow_redirects=True,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        r.raise_for_status()

    except requests.exceptions.RequestException as e:
        st.warning(f"DWDS unavailable for “{word}”: {e}")
        return None

    html = r.text.lower()

    if "ist nicht in unseren" in html and "lexikalischen quellen vorhanden" in html:
        return False

    if "es tut uns leid" in html and "nicht in unseren" in html:
        return False

    return True

def get_dwds_dwb_entries(word: str) -> int | None:
    """
    Get number of DWB entries.
    Returns None if DWDS fails.
    """
    url = f"https://www.dwds.de/wb/dwb/hits"

    try:
        r = requests.get(url, params={"q": word}, timeout=10)
        r.raise_for_status()

        data = r.json()

    except requests.exceptions.RequestException as e:
        st.warning(f"DWB unavailable for “{word}”: {e}")
        return None

    except ValueError:
        st.warning(f"DWB response invalid for “{word}”")
        return None

    if isinstance(data, dict):
        return int(data.get("0", 0))
    
    if isinstance(data, list) and len(data) > 0:
        return int(data[0])

    return 0

def get_dwds_hist_corpora_occurrences(word: str) -> int | None:
    """
    Get historical corpus occurrences.
    Returns None if DWDS fails.
    """
    url = f"https://www.dwds.de/r/hits"

    headers = {"User-Agent": "Mozilla/5.0 (Streamlit DWDS client)"}

    params = {
        "corpus": "dtaxl",
        "q": word
    }

    try:
        r = requests.get(url, params=params, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
    
    except requests.exceptions.HTTPError as e:
        st.warning(f"DWDS sent an HTTP error ({e.response.status_code}) for “{word}”.")  # optionnel
        return None
    
    except requests.exceptions.RequestException:
        st.warning("DWDS is impossible to reach.")
        return None

    if isinstance(data, dict):
        return int(data.get("0", 0))
    
    if isinstance(data, list) and len(data) > 0:
        return int(data[0])

    return 0

### OCR Search ### # 2026-06-27 (15h14)
def search_string_in_ocr(string, lines_by_theme):
    results = defaultdict(list)
    for theme, lines in lines_by_theme.items():
        for line in lines:
            if string in line:
                results[theme].append(line)
    return results

# def load_json(): # 2026-06-11 (11h21) : Pour pouvoir charger de nouveaux fichiers
#     uploaded_file = st.session_state.uploaded_file
#     st.session_state.data = json.load(uploaded_file)
#     st.session_state.token_page = 0

def load_json():

    uploaded_file = st.session_state.uploaded_file

    # Suppression de toutes les clés SAUF celles des widgets système
    # for key in list(st.session_state.keys()):

    #     if key == "uploaded_file":
    #         continue

    #     del st.session_state[key]

    st.session_state.data = json.load(uploaded_file)
    st.session_state.data_id = str(uuid.uuid4())
    st.session_state.token_page = 0
    st.session_state.show_non_candidates = False


PAGE_SIZE = 10 # TODO En fonction de l’écran ? Ou alors en faire un choix utilisateur ? J’améliorerai plus tard, pour moi même, 10 c’est bien avec mon écran.

st.set_page_config(layout="wide")

### LOAD DATA ###
uploaded_file = st.file_uploader("Upload JSON file", type=["json"], key="uploaded_file", on_change=load_json) # 2026-06-11 (11h21) : modification

if uploaded_file:

    if "ocr_lines_by_theme" not in st.session_state: # new 2026-06-27 (14h57)
        with open("ocr_lines_by_theme.json", "r", encoding="utf-8") as f:
            st.session_state.ocr_lines_by_theme = json.load(f)

    if "themes_by_word" not in st.session_state: # 2026-06-27 (23h44)
        with open("themes_by_word.pkl", "rb") as f:
            st.session_state.themes_by_word = pickle.load(f)
    
    # data = json.load(uploaded_file)

    # if "data" not in st.session_state: # 2026-05-30 (16h02) : HYPER important !
    #     st.session_state.data = json.load(uploaded_file)

    # if "token_page" not in st.session_state:
    #     st.session_state.token_page = 0

    # if "show_non_candidates" not in st.session_state:
    #     st.session_state.show_non_candidates = False

    non_candidate_yet = [token for idx, token in st.session_state.data["semantic_tokens"].items() if idx not in st.session_state.data["candidate_tokens"]]

    ### DISPLAY TEXT ###

    st.divider()

    st.subheader("Paragraph metadata")

    colA, colB = st.columns(2)

    with colA:

        st.write(f"**Structure path:** {st.session_state.data.get("structure_path", "")}")

    with colB:

        revision_state_options = ["auto", "in_review", "reviewed"] # TODO À étendre éventuellement

        st.session_state.data["revision_state"] = st.selectbox(
            "revision_state",
            revision_state_options,
            index=revision_state_options.index(st.session_state.data["revision_state"])
        )

    colA, colB = st.columns([4, 1]) # 2026-05-30 (15h39) Je teste

    ### Text of paragraph and translation ###
    with colA:

        col1, col2 = st.columns([4, 1])

        with col1:
            st.write("### Text")
        with col2:
            if st.button("Show semantic tokens"):
                st.session_state.show_non_candidates = not st.session_state.show_non_candidates
                st.rerun()        
        
        # st.write(data["text"])
        html = render_paragraph(st.session_state.data, st.session_state.show_non_candidates) # TODO Changer la clef si je change mes fichiers json !
        st.markdown(html, unsafe_allow_html=True)

        st.write("### Translation")
        st.write(st.session_state.data.get("wikisource_translation"))

        select_options(st.session_state.data, "P", "translation_is_correctly_aligned", "Is the translation well aligned?")

        # st.session_state.data["translation_is_correctly_aligned"] = st.selectbox(
        #     "Is the translation well aligned?",
        #     ["null", "true", "false"],
        #     index=0 if st.session_state.data.get("translation_is_correctly_aligned") is None else (1 if st.session_state.data["translation_is_correctly_aligned"] else 2)#,
        #     # key=f"pos_{i}"
        # )

        # if st.session_state.data["translation_is_correctly_aligned"] == "null":
        #     st.session_state.data["translation_is_correctly_aligned"] = None
        # else:
        #     st.session_state.data["translation_is_correctly_aligned"] = st.session_state.data["translation_is_correctly_aligned"] == "true"

    ### Add tokens ###
    with colB:

        non_candidate_yet = [token for idx, token in st.session_state.data["semantic_tokens"].items() if idx not in st.session_state.data["candidate_tokens"]]

        # st.write("### Add token")
        with st.expander("Add token"):

            search = st.text_input("Search token", value="") # TODO Rajouter un placeholder pertinent

            if search:
                filtered_tokens = [token for token in non_candidate_yet if search.lower() in token["text"].lower()]
            else:
                filtered_tokens = non_candidate_yet
            
            if "previous_search" not in st.session_state:
                st.session_state.previous_search = ""

            if search != st.session_state.previous_search:
                st.session_state.token_page = 0
                st.session_state.previous_search = search

            start = st.session_state.token_page * PAGE_SIZE
            end = start + PAGE_SIZE

            page_tokens = filtered_tokens[start:end]
            st.write (f"Tokens {st.session_state.token_page + 1} / {max(1, (len(filtered_tokens) - 1) // PAGE_SIZE + 1)}") # TODO

            for token in page_tokens:

                if st.button(f"{token['text']} ({token['token_index']})", key=f"add_{token['token_index']}_{st.session_state.data_id}"):

                    token_annotation = { # À adapter si je change ma structure de template !
                        "token_index": token["token_index"], 
                        "is_detected": False, # Important

                        "spacy_pos_is_correct": None, 
                        "spacy_tag_is_correct": None,
                        "spacy_lemma_is_correct": None,
                        "gold_pos": None,
                        "gold_lemma": None,

                        "is_lexically_relevant": None, 
                        "is_context_shifted": None,

                        "contributes_to_a_textual_image": None, 
                        "textual_image_comment": None,

                        "is_metaphorical": None,

                        "is_lexical_metaphor": None,
                        "lexical_metaphor_comment": None,

                        "status": "added" # Important 
                    }

                    st.session_state.data["candidate_tokens"][str(token["token_index"])] = token_annotation
                    st.rerun()
            
            col1, col2 = st.columns(2)
                
            with col1:
                if st.button("⬅️ Previous", disabled=st.session_state.token_page == 0):
                    st.session_state.token_page -= 1
                    st.rerun()

            with col2:
                if st.button("➡️ Next", disabled=end >= len(non_candidate_yet)):
                    st.session_state.token_page += 1
                    st.rerun()

        token_help = """
            Click this button only after having checked all the semantic tokens and insured there is none that should be added anymore.
        """
        # En fait, pour dire qu’on a fini de revoir. Donc si j’en ai ajouté deux et après j’estime que c’est bon, je clique dessus.
        if st.session_state.data.get("no_more_token_to_add"): # 2026-06-27 (15h56)
            st.info("No more token to add")
        elif st.button("No more token to add"):
            st.session_state.data["no_more_token_to_add"] = True # Pour l’instant n’existe pas dans mes templates de base. Et je crois que c’est pas si grave…
        

    st.divider()

    ### TOKEN LEVEL ###

    if "token_filter_lexical" not in st.session_state: # 2026-05-31 (18h05)
        st.session_state.token_filter_lexical = True # Je le mets par défaut !

    toggle_token_filter_lexical_text = (
        "Show all candidate tokens"
        if st.session_state.token_filter_lexical
        else "Show lexically relevant candidate tokens only"
    )

    # TODO Ce serait bien d’afficher les hidden tokens !

    c1, c2 = st.columns([4, 1])

    with c1:
        st.subheader("Tokens")
    with c2:
        st.button(toggle_token_filter_lexical_text, on_click=toggle_token_filter_lexical)

    # for i, token in enumerate(data["tokens"]):
    for idx, token_annotation in st.session_state.data["candidate_tokens"].items():
        token = st.session_state.data["semantic_tokens"][idx]

        if st.session_state.token_filter_lexical and token_annotation["is_lexically_relevant"] is False: # 2026-05-31 (18h09)
            continue # Comme ça on ne l’affiche pas !

        with st.container(border=True):

            c1, c2, c3 = st.columns([2, 1.5, 1.5]) # Je teste diverses proportions

            key = f"mode_{idx}_{st.session_state.data_id}"
            if key not in st.session_state:
                st.session_state[key] = True

            with c1:
                st.write(f"**{token["text"]}**")
                if st.button("Switch view", key=f"btn_{idx}_{st.session_state.data_id}"):
                    st.session_state[key] = not st.session_state[key]

                if st.session_state[key]: # sentence. Échanger si je veux un autre par défaut !
                    st.write("**Sentence**")
                    html = render_sentence(token)
                    st.markdown(html, unsafe_allow_html=True)

                    gold_sentence_translation_is_available = bool(token.get("gold_sentence_translation"))

                    # 2026-05-29
                    st.write("**Sentence translation**")
                    if gold_sentence_translation_is_available:
                        st.caption(token.get("gold_sentence_translation"))
                        st.info("This is the gold alignment of the wikisource translation.")
                    else:
                        st.caption(token.get("sentence_translation"))

                    # TODO On pourrait améliorer celà aussi…

                    with st.expander("DE sentence evaluation"):
                        select_options(token, idx, "de_sentence_eval", "Is the german sentence complete?")

                        if token.get("de_sentence_eval") is False:
                            write_gold(token, idx, "gold_de_sentence", "Gold DE sentence", long=True)
                            write_comment(token, idx, "de_sentence_comment", "Why do you think it failed to give a good sentence?")
                   
                    if not gold_sentence_translation_is_available:                   
                        help_translation = """
                            Please evaluate if the FR sentence(s) proposed as the translation of the DE sentence are correctly chosen among the sentences from the Wikisource translation.

                            We do not ask you to evaluate the quality of the supposedly well aligned sentences, but if the sentences are well aligned, i.e. if they correspond to each other.
                        """                    
                        select_level_options(token, idx, "sentence_translation_eval", "Level of sentence alignment?", help_translation)

                        if token.get("sentence_translation_eval") in ["bad", "partial"]:
                            write_gold(token, idx, "gold_sentence_translation", "Gold sentence translation", long=True)

                else:
                    st.write("**Syntactic group**")
                    html = render_syntactic_group(token) # NEW
                    st.markdown(html, unsafe_allow_html=True)

                    select_quality_options(token_annotation, idx, "syntactic_group_quality", "Quality?") # 2026-05-31 (03h31)

            with c2:

                st.write(f"**Niemann Themes:** {token.get('themes', '')}")
                st.write(f"**POS:** {token["spacy_pos"]}, **LEMMA:** {token["spacy_lemma"]}")

                col1, col2 = st.columns([10, 1])
                if token.get("token_wikisource_translation"):
                    st.write(f"**Token translation:** {token['token_wikisource_translation']}")
                    st.info("This is how the token in translated in the Wikisource translation.")

                    # # En fait non, c’est archi moche…
                    # with col1:
                    #     st.write(f"**Token translation:** {token['token_wikisource_translation']}")
                    #     # st.info("This is how the token in translated in the Wikisource translation.")
                    # with col2:
                    #     with st.popover("?"):
                    #         st.write("This is how the token in translated in the Wikisource translation.")
                    
                    # TODO revoir cette imbrication de if, pas satisfaisant totalement pour l’instant…
                    if token.get("lemma_google_translation"):
                        st.write(f"**Lemma translation:** {token['lemma_google_translation']}")
                        st.info("The lemma translation was obtained with GoogleTranslator.")

                    write_comment(token, idx, "token_translation_comment", "Comment on token/lemma translation") # ⚠ endroit. Pas systématique pour l’instant…
                
                else:

                    if st.button("Show lemma translation", key=f"lemma_{idx}_{st.session_state.data_id}"): # Seulement si utile

                        # TODO sauvegarder la traduction ! Et aussi champ gold… Et pourquoi pas wikisource translation ?
                        lemme_translation = translate_lemme(token["spacy_lemma"])
                        if lemme_translation:
                            st.write(f"**Lemma translation:** {lemme_translation}")
                            st.info("The lemma translation was obtained with GoogleTranslator.")
                            token["lemma_google_translation"] = lemme_translation

                    # TODO Solution temporaire pas satisfaisante.
                    wikisource_translation_of_token = st.text_input("Wikisource translation of token", value="", key=f"wiki_{idx}_{st.session_state.data_id}")
                    if wikisource_translation_of_token:
                        token["token_wikisource_translation"] = wikisource_translation_of_token
                        # st.rerun()

                select_options(token_annotation, idx, "spacy_pos_is_correct", "POS correct?")

                select_options(token_annotation, idx, "spacy_lemma_is_correct", "Lemma correct?")

                if token_annotation["spacy_lemma_is_correct"] is False:
                    write_gold(token_annotation, idx, "gold_lemma", "Gold lemma?")

                if token_annotation["gold_lemma"]:
                    if "themes_gold_lemma" not in token_annotation:
                        token_annotation["themes_gold_lemma"] = st.session_state.themes_by_word[token_annotation["gold_lemma"]]
                    to_write = "**Gold lemma themes:** " + ", ".join(token_annotation["themes_gold_lemma"])
                    st.markdown(to_write)

                # if st.button("Search in lexical resources", key=f"lexical_search_{idx}"): # 2026-06-01 (11h29)
                # TODO à améliorer…
                with st.form(key=f"lex_form_{idx}_{st.session_state.data_id}"):

                    to_search = st.text_input("Form to search in lexical resources", value=token["spacy_lemma"], key=f"lexical_search_{idx}_{st.session_state.data_id}")
                    submitted = st.form_submit_button("Search in lexical resources", key=f"search_btn_{idx}_{st.session_state.data_id}")

                if submitted and to_search:
                    
                    if token.get("lexical_search") and isinstance(token["lexical_search"], dict) and token["lexical_search"].get(to_search):
                        to_search_results = token["lexical_search"][to_search]
                    else: # Pour éviter de recalculer si information déjà disponible
                        to_search_results = {
                            "is_in_wiktionary": word_is_in_wiktionary_de(to_search),
                            "is_in_dwds": word_is_in_dwds(to_search),
                            "dwds_historical_corpora_occurrences": get_dwds_hist_corpora_occurrences(to_search),
                            "dwb_entries": get_dwds_dwb_entries(to_search)
                        }

                        if token.get("lexical_search") and isinstance(token["lexical_search"], dict):
                            token["lexical_search"][to_search] = to_search_results
                        else:
                            token["lexical_search"] = {
                                to_search: to_search_results
                            }
                        
                    if to_search_results["is_in_wiktionary"]:
                        st.success(f'"{to_search}" exists in the german Wiktionary.')
                    else:
                        st.error(f'"{to_search}" wasn’t found in the german Wiktionary.')
                    if to_search_results["is_in_dwds"]:
                        st.success(f'"{to_search}" exists in the DWDS.')
                    else:
                        st.error(f'"{to_search}" wasn’t found in the DWDS.')
                        dwb_hits = to_search_results["dwb_entries"] # Pour le dictionnaire des frères Grimm
                        st.write(f"{dwb_hits} {'entry' if dwb_hits in [0, 1] else 'entries'} in the DWB.")
                        hist_corpora_occurences = to_search_results["dwds_historical_corpora_occurrences"]
                        st.write(f"{hist_corpora_occurences} occurrences in the DWDS historical corpora.")                    


                
                if token_annotation["is_detected"] is False:
                    if token.get('themes', '') in ["No entry found.", ""]: # 2026-06-27 (15h05)
                        # Il est alors pertinent de consulter le fichier ocr_lines_by_theme.json

                        if "ocr_check" not in token_annotation:
                            token_annotation["ocr_check"] = {}
                            token_annotation["ocr_check"][token["spacy_lemma"]] = search_string_in_ocr(token["spacy_lemma"], st.session_state.ocr_lines_by_theme)
                        to_write = ""

                        for form, results in token_annotation["ocr_check"].items():
                            if results == {}:
                                to_write += f"No match found in the OCR files for `{form}`.\n\n"
                                continue
                            elif form != token["spacy_lemma"]:
                                to_write += f"**OCR Search for `{form}`:**\n\n"
                            for theme, lines in results.items():
                                lines_to_write = [f"* `{line}`" for line in lines]
                                to_write += f"**{theme}:**\n\n{'\n'.join(lines_to_write)}\n\n"
                        
                        #for theme, lines in token_annotation["ocr_check"].items():
                        #    lines_to_write = [f"* `{line}`" for line in lines]
                        #    to_write += f"**{theme}:**\n\n{'\n'.join(lines_to_write)}\n\n"
                        
                        #to_write = to_write if to_write else f"No match found in the OCR files for “{token['spacy_lemma']}”"
                        with st.container(border=True):
                            st.caption("OCR Search")
                            st.markdown(to_write)
                            
                            if token_annotation["ocr_check"][token["spacy_lemma"]] == {}:
                                to_search = st.text_input("Form to search in the OCRized Niemann", key=f"ocr_search_{idx}_{st.session_state.data_id}")

                                if st.button("Search", key=f"search_{idx}_{st.session_state.data_id}"):
                                    token_annotation["ocr_check"][to_search] = search_string_in_ocr(to_search, st.session_state.ocr_lines_by_theme,)
                                    st.rerun()

                    select_undetected_cause_options(token, token_annotation, idx) # 2026-06-27 (16h27)
                    
                    token_annotation["detection_comment"] = st.text_area(
                        "Why is the token not detected?",
                        value=token_annotation.get("detection_comment", ""),
                        key=f"detection_comment_{idx}_{st.session_state.data_id}" 
                    )

                # TODO ajouter gold si pas correct ! hehe !

            with c3:

                select_options(token_annotation, idx, "is_lexically_relevant", "Lexically relevant?")
                write_comment(token_annotation, idx, "lexical_relevance_comment", "Comment") # 2026-05-31 (03h08)

                select_options(token_annotation, idx, "is_context_shifted", "Contextually shifted?")

                select_options(token_annotation, idx, "contributes_to_a_textual_image", "Contributes to textual image?")
                write_comment(token_annotation, idx, "textual_image_comment", "Comment")

                select_options(token_annotation, idx, "is_metaphorical", "Metaphor?")
                write_comment(token_annotation, idx, "metaphor_comment", "Comment")

                select_options(token_annotation, idx, "is_lexical_metaphor", "Lexical metaphor?")
                write_comment(token_annotation, idx, "lexical_metaphor_comment", "Comment")

    st.divider()

    ### SAVE ###

    # Ne marche que si un seul download bouton

    st.markdown("""
    <style>
    div[data-testid="stDownloadButton"] button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 9999;
        width: auto;

        border: none;
        padding: 12px 18px;
        border-radius: 12px;

        font-weight: 600;
        font-size: 14px;

        box-shadow: 0 8px 20px rgba(79, 70, 229, 0.35);
        cursor: pointer;

        transition: all 0.2s ease-in-out;
    }

    /* hover */
    div[data-testid="stDownloadButton"] button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 25px rgba(79, 70, 229, 0.45);
    }

    /* click */
    div[data-testid="stDownloadButton"] button:active {
        transform: translateY(0px) scale(0.98);
        box-shadow: 0 6px 15px rgba(79, 70, 229, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

    st.download_button(
        label="Save this paragraph",
        data=json.dumps(st.session_state.data, indent=2, ensure_ascii=False),
        file_name=f"{st.session_state.data['paragraph_id']}.json",
        mime="application/json"
    )




