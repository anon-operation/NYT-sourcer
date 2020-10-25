import streamlit as st
import pandas as pd
import numpy as np
import pickle
#import plotly.figure_factory as ff
import plotly.express as px
import plotly.io as pio
import datetime
pio.renderers.default = 'firefox'
import sqlite3
from sqlite3 import Connection
import sqlalchemy
from sqlalchemy import create_engine
import time

class Article:
    def __init__(self):
        self.sources = {}
        return;

class StoryMetadata:
    def __init__(self):
        self.pubDate = ""
        self.author = []
        self.section = ""
        self.url = ""
        self.sources = {}
        return;



sqlfilename = "NYT.sqlite"
engineString='sqlite:///'+sqlfilename

@st.cache(allow_output_mutation=True)
def get_connection(engineString):
    engi = create_engine(engineString,connect_args={'check_same_thread': False})
    connection=engi.raw_connection()
    return connection

@st.cache
def createQuery(fieldName,queryFieldName,queryValue):
    qString = "SELECT "+ fieldName + " FROM " + "ARTICLES"
    qString += " WHERE " + queryFieldName + queryValue
    return qString

@st.cache(allow_output_mutation=True)
def load_data(queryString):
    with st.spinner('Loading Data...'):
        time.sleep(0.5)
        df = pd.read_sql_query(queryString, get_connection(engineString))
        try:
            df['Date']=pd.to_datetime(df['Date'], format='%Y-%m-%dT%H:%M:%S')
        except:
            RanVar=0
    return df

@st.cache
def highlight_name1(val):
    strung=str(val)
    loweredVal=strung.lower()
    loweredInput=name_user_input.lower()
    if loweredInput in loweredVal:
        color = 'red'
    else:
        color = 'black'
    return 'color: %s' % color

st.title("The Sourcer...beta version")

query = createQuery("*","Count"," ==1 ;")
df = load_data(query)
#st.write(df)

############ Graphing
st.header("Find names that appear in news stories")

########### sidebar
st.sidebar.header("Welcome to the Sourcer App")
st.sidebar.subheader("This app shows names that appear in the text of New York Times Articles.")
moreInfo=st.sidebar.button("More info")
if moreInfo:
    st.sidebar.subheader("This app began as a question:")
    st.sidebar.subheader( "\"Is there a quick way to figure out who is mentioned in a New York Times story?\"")
    st.sidebar.subheader("From there the project grew...and is still growing!")
    st.sidebar.subheader("Each day the database of included articles grows. They come from the New York Times' front page.")
    st.sidebar.subheader("Additionally, I'm working to improve the accuracy of the name recognition, so that names like \"Mr. Trump\" and \"Donald Trump\" are seen as the same name and to exclude place names from recognition.")
    st.sidebar.subheader("The source code is availible for inspection at: https://github.com/anon-operation/NYT-Sourcer.git")
##
#################
##
modifyChart=st.checkbox("Click here for more oprtions")
if modifyChart:
    section_selectbox=st.selectbox("What section would you like to see?",
                                   ("All sections", "Health", "U.S.", "Business", "Upshot",
                                    "Magazine", "Briefing", "Podcasts",
                                    "Opinion", "N.Y. Region", "World",
                                    "Climate", "Dining", "Technology",
                                    "Style", "Sports", "Arts"))
    attribute_selectbox=st.selectbox("Type of attribute", ("All","NLTK", "High", "Low", "Known"))
    if attribute_selectbox=="All":
        st.text(attribute_selectbox+" means that all names from the given section(s) and time period will be displyed.")
        attributeChoice='%'
    if attribute_selectbox=="NLTK":
        st.text(attribute_selectbox+" means that all names identified by the Natural Language processor will be displyed.")
        attributeChoice=attribute_selectbox.lower()
    if attribute_selectbox=="High":
        st.text(attribute_selectbox+" means that all names found near the keywords 'said', 'says, 'according', 'explains', 'explained', and 'explain' will be displyed.")
        attributeChoice=attribute_selectbox.lower()
    if attribute_selectbox=="Low":
        st.text(attribute_selectbox+" means that all names found near the keywords 'recalls', 'recalled', 'thinks', 'think', 'describe', 'agreed', 'agrees', 'describes', 'described', 'points', 'pointed', 'point', 'indicates', 'indicate', and 'indicated' will be displyed.")
        attributeChoice=attribute_selectbox.lower()
    elif attribute_selectbox=="Known":
        st.text(attribute_selectbox+" means that all names that match previously identified names (withtin the month) will be displyed.")
        attributeChoice=attribute_selectbox.lower()
    startDate=st.date_input("Start date", pd.to_datetime("2020-09-29"))
    qDate1 = str((str(startDate))+"T00:00:00")
    endDate=st.date_input("End date", pd.to_datetime("2020-10-10"))
    qDate2 = str((str(endDate))+"T24:59:59")
    moreLess=st.radio("",('Show names that appear MORE than selected number of times', 'Show names that appear LESS than selected number of times'))
    sliderVal=st.slider("", min_value=1, max_value=100, value=50, step=1)
    if moreLess=="Show names that appear MORE than selected number of times":
        st.text("Show only names that appear more than "+str(sliderVal)+" times.")

    else:
        st.text("Show only names that appear less than "+str(sliderVal)+" times.")

    if startDate <= endDate:
            if section_selectbox=="All sections":
                breakDownSwitch=st.checkbox("Break the data down by section")
                if breakDownSwitch:
                    query="SELECT * FROM ARTICLES WHERE Date BETWEEN "+"'"+qDate1+"'"+" AND "+"'"+qDate2+"'"+" AND Type LIKE  "+"'"+attributeChoice+"'"+" ;"       
                    df= load_data(query)
                    df['Tally']=df.groupby('Name')['Name'].transform('count')
                    if moreLess=="Show names that appear MORE than selected number of times":
                        df=df[df['Tally'] > sliderVal]
                    else:
                        df=df[df['Tally'] < sliderVal]
                    fig=px.bar(df, x="Name", y="Count", color="Section",
                        hover_data=["Name","Title", "Section"],
                        labels={"Name":"Name", "Count":"Number of articles the name appers in"})
                    fig.update_layout(xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig, use_container_width=False)
                else:
                    query="SELECT Name, count(*) FROM ARTICLES WHERE Date BETWEEN "+"'"+qDate1+"'"+" AND "+"'"+qDate2+"'"+" AND Type LIKE  "+"'"+attributeChoice+"'"+" GROUP BY Name ;"
                    df= load_data(query)
                    df.columns=['Name', 'Number']
                    if moreLess=="Show names that appear MORE than selected number of times":
                        df1=df[df['Number'] > sliderVal]
                    else:
                        df1=df[df['Number'] < sliderVal]
                    df1 = df1.sort_values('Number', ascending=True)
                    fig=px.bar(df1, x="Name", y="Number",
                               hover_data=["Name"],
                               labels={"Name":"Name", "Number":"Number of articles the name appers in"})
                    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
                    st.plotly_chart(fig, use_container_width=True)
            else:
                lowercaseSelection=section_selectbox.lower()
                if lowercaseSelection=="u.s.":
                    lowercaseSelection="us"
                elif lowercaseSelection=="n.y. region":
                    lowercaseSelection="nyregion"
                query="SELECT Name, count(*) FROM ARTICLES WHERE Date BETWEEN "+"'"+qDate1+"'"+" AND "+"'"+qDate2+"'"+" AND Type LIKE  "+"'"+attributeChoice+"'"+" AND Section LIKE "+"'"+lowercaseSelection+"'"+" GROUP BY Name ;"
                df= load_data(query)
                df.columns=['Name', 'Number']
                if moreLess=="Show names that appear MORE than selected number of times":
                    df1=df[df['Number'] > sliderVal]
                else:
                    df1=df[df['Number'] < sliderVal]
                df1 = df1.sort_values('Number', ascending=True)
                fig=px.bar(df1, x="Name", y="Number",
                           hover_data=["Name"],
                           labels={"Name":"Name", "Number":"Number of articles the name appers in"})
                fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Error: The end date must be after the start date.")
else:
    breakDownSwitch1=st.checkbox("Break the data down by section")
    if breakDownSwitch1:
        st.text("Chart shows names that appear more than 100 times in the last few months.")
        query1="SELECT * FROM ARTICLES WHERE Type LIKE 'nltk';"
        df= load_data(query1)
        df['Tally']=df.groupby('Name')['Name'].transform('count')
        df=df[df['Tally'] > 100]
        fig=px.bar(df, x="Name", y="Count", color="Section",
                    hover_data=["Name","Title", "Section"],
                    labels={"Name":"Name", "Count":"Number of articles the name appers in"})
        fig.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.text("Chart shows names that appear more than 100 times.")
        ##
        query="SELECT Name, count(*) FROM ARTICLES WHERE Type LIKE 'nltk' GROUP BY Name;"
        # HAVING COUNT(1)>100 AND Type LIKE 'nltk' ;"
        df= load_data(query)
        df.columns=['Name', 'Number']
        df1=df[df['Number'] > 100]
        df1 = df1.sort_values('Number', ascending=True)
        fig=px.bar(df1, x="Name", y="Number",
                    hover_data=["Name"],
                    labels={"Name":"Name", "Number":"Number of articles the name appers in"})
        fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig, use_container_width=True)


######################
##

################################# Tabling
##
##showData=st.checkbox("Show the raw data")
##
##if(showData==True):
##    if modifyChart:
########## Sort data based on user's search term
##        matchGraph=st.checkbox("Show data displayed in selected section")
##        if matchGraph:
##            if (section_selectbox =="All sections"):
##                st.subheader('Raw Data from '+section_selectbox+' of New York Times')
##            else:
##                st.subheader('Raw Data from the '+section_selectbox+' section of New York Times')
##            name_user_input = st.text_input("Search for a name.", "")
##            lowerName=name_user_input.lower()
##            restOf=df3[~df3['Name'].str.contains(lowerName)]
##            sortedDf=pd.concat([indexList, restOf], ignore_index=True, sort=False)
##            st.dataframe(sortedDf.style.applymap(highlight_name1))
##        else:
##            st.subheader('Raw Data from entire database')
##            name_user_input = st.text_input("Search for a name.", "")
##            lowerName=name_user_input.lower()
##            indexList=df[df['Name'].str.contains(lowerName)]
##            restOf=df[~df['Name'].str.contains(lowerName)]
##            sortedDf=pd.concat([indexList, restOf], ignore_index=True, sort=False)
##            st.dataframe(sortedDf.style.applymap(highlight_name1))
##    else:
##        st.subheader('Raw Data from entire database')
##        name_user_input = st.text_input("Search for a name.", "")
##        lowerName=name_user_input.lower()
##        indexList=df[df['Name'].str.contains(lowerName)]
##        restOf=df[~df['Name'].str.contains(lowerName)]
##        sortedDf=pd.concat([indexList, restOf], ignore_index=True, sort=False)
##        st.dataframe(sortedDf.style.applymap(highlight_name1))
##
##
################ TIMESERIES
name_user_input = st.text_input("Search for a name.", "Donald Trump")
searchName=name_user_input.lower()
query="SELECT Name,Date,Title,Type,Section, Count FROM ARTICLES;"
seriesDf= load_data(query)
seriesDf['Name']=seriesDf['Name'].str.lower()
seriesDf.loc[:,'Name']=seriesDf.loc[:,'Name'].str.replace("`|’", "'", regex=True)
serIndexList=seriesDf[seriesDf['Name'].str.contains(searchName)]
nameFrame=serIndexList

serIndexList['Week/Year'] = serIndexList['Date'].apply(lambda x: "%d/%d" % (x.week, x.year))
serIndexList=serIndexList.groupby(['Week/Year', 'Name']).size()
serIndexList=serIndexList.reset_index(level=['Week/Year', 'Name'])
serIndexList=serIndexList.groupby(['Week/Year']).sum()
serIndexList["Week"]=serIndexList.index
serIndexList.columns=['Count',"Week"]
labString="Number of articles the name "+name_user_input+" appears in "
labDict={"Week":"Week / Year", "Count":labString}
timefig=px.bar(serIndexList, x='Week', y='Count',
               hover_data=['Week', 'Count'],
                labels=labDict)
st.plotly_chart(timefig, use_container_width=True)
st.subheader("Data displayed in chart")
st.dataframe(nameFrame.style.applymap(highlight_name1))
st.subheader("")
st.subheader("")

















##
##
##serIndexList['Week/Year'] = serIndexList['Date'].apply(lambda x: "%d/%d" % (x.week, x.year))
##look=serIndexList.groupby(['Week/Year', 'Name']).size()
##look=look.reset_index(level=['Week/Year', 'Name'])
##del look['Name']
##check=look.groupby(['Week/Year']).sum()
##check["Week"]=check.index
##check.columns=['Count',"Week"]
##labString="Number of articles the name "+name_user_input+" appears in."
##
##labDict={"Week":"Week / Year", "Count":labString}
##timefig=px.bar(check, x='Week', y='Count',
##                labels=labDict)
##st.plotly_chart(timefig, use_container_width=True)
##

##
##timefig=px.line(look, x='Week/Year', y=0)
##st.plotly_chart(timefig, use_container_width=True)



##st.plotly_chart(timefig, use_container_width=True)
##
##
##st.dataframe(serIndexList.style.applymap(highlight_name1))
##
##



    
################## Search by Article
##st.text("")
st.subheader("Search for a specific article")
article_user_input = st.text_input("Search for an article.", "")
lowerArtName=article_user_input.lower()
query="SELECT Title,Name,Date,Type,Section FROM ARTICLES ;"
articleDf= load_data(query)

##articleDf=pd.DataFrame(data)
##articleDf['Date']=pd.to_datetime(articleDf['Date'], format='%Y-%m-%dT%H:%M:%S')
articleDf['Title']=articleDf['Title'].str.lower()
articleDf.loc[:,'Title']=articleDf.loc[:,'Title'].str.replace("`|’", "'", regex=True)
artIndexList=articleDf[articleDf['Title'].str.contains(lowerArtName)]
if artIndexList.empty:
    st.error("There are no article titles that contain "+article_user_input)
else:
    st.dataframe(artIndexList)
    printList=st.button("Get list of names in article(s) with \""+article_user_input+"\" in the title")
    if printList:
        listDf=artIndexList['Name']
        st.text("You can highlight and copy this list of names:")
        for name in listDf:
            st.text(name)
##
## 
##
##
##                lowercaseSelection=section_selectbox.lower()
##                if lowercaseSelection=="u.s.":
##                    lowercaseSelection="us"
##                elif lowercaseSelection=="n.y. region":
##                    lowercaseSelection="nyregion"
##                query="SELECT * FROM ARTICLES WHERE Date BETWEEN "+"'"+qDate1+"'"+" AND "+"'"+qDate2+"'"+" AND Type LIKE  "+"'"+attributeChoice+"'"+" AND Section LIKE "+"'"+lowercaseSelection+"'"+" ;"
##                df= load_data(query)
##                df['Tally']=df.groupby('Name')['Name'].transform('count')
##                if moreLess=="Show names that appear MORE than selected number of times":
##                    df=df[df['Tally'] > sliderVal]
##                else:
##                    df=df[df['Tally'] < sliderVal]
##                fig=px.bar(df, x="Name", y="Count", color="Section",
##                    hover_data=["Name","Title", "Section"],
##                    labels={"Name":"Name", "Count":"Number of articles the name appers in"})
##                fig.update_layout(xaxis={'categoryorder':'total descending'})
##                st.plotly_chart(fig, use_container_width=False)
##
##
##        else:
##            
##            if section_selectbox=="All sections":
##                query="SELECT Name, count(*) FROM ARTICLES WHERE Date BETWEEN "+"'"+qDate1+"'"+" AND "+"'"+qDate2+"'"+" AND Type LIKE  "+"'"+attributeChoice+"'"+" GROUP BY Name ;"
##                df= load_data(query)
##                df.columns=['Name', 'Number']
##                if moreLess=="Show names that appear MORE than selected number of times":
##                    df1=df[df['Number'] > sliderVal]
##                else:
##                    df1=df[df['Number'] < sliderVal]
##                df1 = df1.sort_values('Number', ascending=True)
##                fig=px.bar(df1, x="Name", y="Number",
##                           hover_data=["Name"],
##                           labels={"Name":"Name", "Number":"Number of articles the name appers in"})
##                fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})
##                st.plotly_chart(fig, use_container_width=True)
