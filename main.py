import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from matplotlib.figure import Figure
from pymed import PubMed
from wordcloud import WordCloud

st.title('Data Visualization - PubMed')
st.markdown("""
Trabalho de conclusão de curso feito por Mateus Paiva dos Reis [mateuspaivareis25@gmail.com]
""")
geolocator = Nominatim(user_agent="tcc")
st.sidebar.header('Filtro')
qtdeResultados = st.sidebar.text_input("Quantidade Resultados", 10)
meshSelecionado = st.sidebar.selectbox("Tema", list(
    ["Lung Diseases", "Otorhinolaryngologic Diseases", "Hematologic Diseases", "Ear Diseases", "Dent Disease",
     "Mikulicz' Disease", "Pharyngeal Diseases"]))
anoSelecionado = st.sidebar.selectbox("Ano", list(reversed(range(1950, 2021))))

# Create a GraphQL query in plain text
query = '(("' + str(anoSelecionado) + '/01/01"[Date - Publication] : "' + str(
    anoSelecionado) + '/12/31"[Date - Publication])) AND (' + meshSelecionado + '[MeSH Terms])'
pubmed = PubMed(tool="PbMedSearcher", email="myemail@ccc.com")
results = pubmed.query(query, max_results=int(qtdeResultados))

articleList = []
articleInfo = []
authorsInfo = []
keywordInfo = []

for article in results:
    # Print the type of object we've found (can be either PubMedBookArticle or PubMedArticle).
    # We need to convert it to dictionary with available function

    articleDict = article.toDict()
    articleList.append(articleDict)

# Generate list of dict records which will hold all article details that could be fetch from PUBMED API
for article in articleList:
    # Sometimes article['pubmed_id'] contains list separated with comma - take first pubmedId in that list -
    # thats article pubmedId
    pubmedId = article['pubmed_id'].partition('\n')[0]

    # Append article info to dictionary
    articleInfo.append({u'pubmed_id': pubmedId,
                        u'title': article['title'],
                        u'keywords': article['keywords'],
                        u'journal': article['journal'],
                        u'abstract': article['abstract'],
                        u'conclusions': article['conclusions'],
                        u'methods': article['methods'],
                        u'results': article['results'],
                        u'copyrights': article['copyrights'],
                        u'doi': article['doi'],
                        u'publication_date': article['publication_date'],
                        u'authors': article['authors']})
    for autor in article['authors']:
        authorsInfo.append({u'pubmed_id': pubmedId,
                            u'lastname': autor['lastname'],
                            u'firstname': autor['firstname'],
                            u'affiliation': autor['affiliation']}
                           )

    for keyword in article['keywords']:
        keywordInfo.append({u'pubmed_id': pubmedId,
                            u'keyword': keyword}
                           )

palavrasChaves = pd.DataFrame.from_dict(keywordInfo)
artigos = pd.DataFrame.from_dict(articleInfo)
autores = pd.DataFrame.from_dict(authorsInfo)

stop_words_v1 = ['s', 've', 'll', 'm', 're', 't', 'd', 'a', 'i', 'l', 'know', 'could', 'would']

palavrasChaves.replace(np.nan, '', regex=True)
wc = WordCloud(stopwords=stop_words_v1, background_color='white')
kw = " ".join(keyword for keyword in palavrasChaves.dropna().keyword)
wc = wc.generate(kw)
# Display the generated image:
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
st.pyplot(plt)

artigosDf = pd.DataFrame(artigos, columns=['title', 'journal', 'abstract', 'conclusions'])
autoresDf = pd.DataFrame(autores, columns=['firstname', 'lastname', 'affiliation'])
autoresDf['nomeSobrenome'] = autoresDf['firstname'] + ' ' + autoresDf['lastname']

st.markdown("A busca retornou um total de **{} artigos que foram escritos por mais de {} autores,** sendo {} como o "
            "autor com mais artigos. existem {} afiliações participantes da pesquisa nesse tema.".format(
    len(artigos['pubmed_id'].unique()), len(autoresDf['nomeSobrenome'].unique()), autoresDf['nomeSobrenome'].mode()[0],
    len(autoresDf['affiliation'].unique())))

author_gender_df = pd.DataFrame(
    autoresDf['affiliation'].str.split(',').str[0].value_counts(normalize=True).head(10)).reset_index()
fig = Figure()
ax = fig.subplots()
sns.barplot(x=author_gender_df['affiliation'],
            y=author_gender_df['index'], color="green", ax=ax)
ax.set_ylabel('Afiliação')
ax.set_xlabel('Percentage')
st.pyplot(fig)

author_df = pd.DataFrame(autoresDf['nomeSobrenome'].value_counts(normalize=True).head(10)).reset_index()
fig = Figure()
ax = fig.subplots()
sns.barplot(x=author_df['nomeSobrenome'],
            y=author_df['index'], color="green", ax=ax)
ax.set_ylabel('nomeSobrenome')
ax.set_xlabel('Percentage')
st.pyplot(fig)

palavrasChavesDf = pd.DataFrame(palavrasChaves, columns=['keyword'])

geocode_with_delay = RateLimiter(geolocator.geocode, min_delay_seconds=1)

autores['possivelEnd1'] = autores['affiliation'].str.split(',').str[-1]
autores['temp'] = autores['possivelEnd1'].dropna().apply(geocode_with_delay)
autores["coords"] = autores['temp'].dropna().apply(lambda loc: tuple(loc.point) if loc else None)
autores[['lat', 'lon', 'altitude']] = pd.DataFrame(autores['coords'].tolist(), index=autores.index)

autores['lat'] = autores['lat'].astype(float)
autores['lon'] = autores['lon'].astype(float)
midpoint = (np.average(autores["lat"]), np.average(autores["lon"]))
dataframeCoord = pd.DataFrame(autores, columns=['lat', 'lon'])
dataframeCoord.apply(pd.to_numeric, errors='coerce')
dataframeCoord = dataframeCoord.dropna()

st.map(dataframeCoord, zoom=12)

st.write("DESENV - DATAFRAMES")
st.write("Datas de Publicação Encontradas")
st.write(artigos['publication_date'])
st.write("Palavras Chaves Encontradas")
st.dataframe(palavrasChavesDf)
st.dataframe(dataframeCoord)
st.dataframe(autores)
st.dataframe(autoresDf)
st.dataframe(artigosDf)
st.dataframe(artigos)
st.dataframe(autoresDf)
