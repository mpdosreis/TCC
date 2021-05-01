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

geolocator = Nominatim(user_agent="mateuspaivareis25@gmail.com")

st.sidebar.header('Filtro')
qtdeResultados = st.sidebar.text_input("Quantidade Resultados", 3)
meshSelecionado = st.sidebar.selectbox("Tema", list(
    [ "Otorhinolaryngologic Diseases", "Hematologic Diseases",  "Dent Disease", "Mikulicz' Disease", "Pharyngeal Diseases"]))
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

st.image("https://www2.ifsc.usp.br/portal-ifsc/wp-content/uploads/2019/04/uff500.jpg", width=150)
st.title("PubMedDataView")
st.markdown("**Busca simplificada no PubMed para a visualização das informações sobre grupos de pesquisa**")
st.markdown("---")
st.markdown("Trabalho de conclusão de curso apresentado ao curso de Bacharelado em Sistemas de Informação da Universidade Federal Fluminense como requisito parcial para conclusão do curso.")
st.markdown('A visualização abaixo é proveniente da busca de **{}** artigos via API do PubMed filtrados pelo ano de publicação **{}**, pelo tema **{}**'.format( str(qtdeResultados), str(anoSelecionado), meshSelecionado ))
st.markdown('A nuvem de palavra abaixo foi gerada utilizando {} palavras chave dos artigos encontrados:'.format(len(kw)))

st.subheader('**Nuvem de Palavras-Chave**')
wc = wc.generate(kw)
# Display the generated image:
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
st.pyplot(plt)

artigosDf = pd.DataFrame(artigos, columns=['title', 'journal', 'abstract', 'conclusions'])
autoresDf = pd.DataFrame(autores, columns=['firstname', 'lastname', 'affiliation'])
autoresDf['nomeSobrenome'] = autoresDf['firstname'] + ' ' + autoresDf['lastname']

st.markdown("Os artigos encontrados foram escritos por mais de **{}** autores diferentes, sendo **{}** como o "
            "autor com mais artigos.O grafico abaixo indica o percentual de participação do autor nos artigos retornados".format(
     len(autoresDf['nomeSobrenome'].unique()), autoresDf['nomeSobrenome'].mode()[0]))

author_df = pd.DataFrame(autoresDf['nomeSobrenome'].value_counts(normalize=True).head(10)).reset_index()
fig = Figure()
ax = fig.subplots()
sns.barplot(x=author_df['nomeSobrenome'],
            y=author_df['index'], color="green", ax=ax)
st.subheader('**Os 10 autores com maior percentual de participação na busca realizada**')
ax.set_ylabel('Autor')
ax.set_xlabel('Percentual de Participação')


st.pyplot(fig)


st.markdown(' Estes autores são provenientes de {} afiliações diferentes, sendo {} com o maior percentual de participação na busca realizada. O grafico abaixo lista as 10 maiores afiliações na busca realizada. O mapa indica as suas posições no mundo'.format(len(autoresDf['affiliation'].unique()), autoresDf['affiliation'].mode()[0].split(',')[0]))

afiliacaoDf = pd.DataFrame(
    autoresDf['affiliation'].str.split(',').str[0].value_counts(normalize=True).head(10)).reset_index()
fig = Figure()
ax = fig.subplots()
sns.barplot(x=afiliacaoDf['affiliation'],
            y=afiliacaoDf['index'], color="green", ax=ax)
ax.set_ylabel('Afiliação')
ax.set_xlabel('Percentual de Participação')
st.subheader('**As 10 afiliações de maior percentual de participação na busca realizada**')
st.pyplot(fig)

geocode_with_delay = RateLimiter(geolocator.geocode, min_delay_seconds=5)

st.warning('Por utilizar o Nomatim, um serviço gratuito de Geolocalização, o mapa pode demorar alguns minutos para ser exibido.')
st.subheader('**Mapa com as localizações das afiliações**')


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
#
# st.write("DESENV - DATAFRAMES")
# st.write("Datas de Publicação Encontradas")
# st.write(artigos['publication_date'])
# st.write("Palavras Chaves Encontradas")
# st.dataframe(dataframeCoord)
# st.dataframe(autores)
# st.dataframe(autoresDf)
# st.dataframe(artigosDf)
# st.dataframe(artigos)
# st.dataframe(autoresDf)
