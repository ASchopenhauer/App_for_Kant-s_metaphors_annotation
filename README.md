# Presentation
This repository contains the source code of the Streamlit application developed for my master’s thesis. The repository containing the full work on the thesis itself is currently private.

To provide some context, my master's thesis focuses on the detection of metaphors in Kant's practical philosophy. To this end, we first attempt to identify content words that are used with a concrete meaning or whose meaning may indicate a thematic shift within a paragraph relative to the domain of practical philosophy.

For this purpose, we extracted lists of nouns, adjectives, and verbs from the following vocabulary book:

> Raymond-Fred NIEMANN, _Les mots allemands: Deutsch-französischer Wortschatz nach Sachgruppen_, Paris, 1997

In this work, vocabulary is organized by thematic categories. Using computational methods, we generated lists of nouns, verbs, and adjectives grouped by theme. We also created metadata indicating, for each word, all the thematic categories in which it appears in Niemann's book, since many words are polysemous and may belong to several themes.

Among these themes, we selected those that appeared to be relatively distant from practical philosophy and from Kant's treatment of the subject. We then detect words belonging to the selected themes on a paragraph-by-paragraph basis. The detection process relies on the predicted lemmas and parts of speech of the words in a paragraph rather than on their surface orthographic forms.

The present application is intended to support a pilot annotation and evaluation phase of the results obtained through our detection process. At this stage, no definitive nor strict annotation criteria or guidelines have been established. One of the main objectives of this initial annotation phase is precisely to gain a better understanding of our requirements, to help refine the research questions, identify relevant criteria, and clarify what should count as a metaphorical expression in the context of Kant's practical philosophy

# Use
Donwload a JSON file from the `pilot` directory, either from `Templates` or `Reviewed` on your computer.

Then load that file in the streamlit app [here](https://appforkant-smetaphorsannotation-4zfixsg2qy6zshxmds3vbc.streamlit.app/).
