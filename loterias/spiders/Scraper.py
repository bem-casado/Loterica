import scrapy 
import json
import pandas as pd
import ast
import sys
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import sys
import datetime
import time
import re
import ast
import os
from bs4 import BeautifulSoup

class scraper(scrapy.Spider):
    name="loterias"
    start_urls=['https://servicebus2.caixa.gov.br/portaldeloterias/api/loterias']
    base_link="https://servicebus2.caixa.gov.br/portaldeloterias/api/locais-da-sorte?modalidade={}&concurso={}"
    # input=['MEGA_SENA']
    # recipients = ['adilayub101@gmail.com']  #send to
    your_email="confereresultados@gmail.com" #your email
    password= 'nehhzsoewnsjvgfo' #This password is not your email password but your app password.


    def __init__(self):
        self.output_filename=sys.argv[3]
        self.input_df=pd.read_excel(".\\Input.xlsx")

    def send_email(self,df,subject,rep):
        send_mail=True
        number=int(re.findall("(\d+)",subject)[0])
        company_name=re.findall("(.*?) - ",subject)[0]
        today=datetime.date.today()
        yesterday=today - datetime.timedelta(days=1)
        # day_before_yesterday=today - datetime.timedelta(days=2)
        # try:
        #     os.remove(".\\"+day_before_yesterday+".json")
        # except:
        #     pass
        try:
            file=open(f"{yesterday}.json","r")
            data=json.load(file)
            file.close()
            # print(data[company_name]+1 , number)
            if(data[company_name]+1 <= number):
                send_mail=True
            else:
                send_mail=False
        except Exception as e:
            # print(str(e))
            pass
        try:
            file=open(f"{today}.json","r")
            data=json.load(file)
            file.close()
        except:
            try:
                file=open(f"{yesterday}.json","r")
                data=json.load(file)
                file.close()    
            except:
                data={}
        data[company_name]=number
        with open(f"{today}.json", 'w') as fp:
            json.dump(data, fp)
        
        # send_mail=False
        if(send_mail):
            emaillist = [rep]
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = self.your_email


            html = """\
            <html>
            <head></head>
            <body>
                {}
            </body>
            </html>
            """.format(df.to_html(index=False))

            part1 = MIMEText(html, 'html')
            msg.attach(part1)

            # with smtplib.SMTP('localhost', 1025) as server:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.your_email,self.password)
                server.sendmail(msg['From'], emaillist, msg.as_string())
                print("Successfully sent email")
        else:
            print(f"{company_name} -  has not been updated since last time")


    def closed(self,reason):
        print("CLOSED")
        selected=[]
        ffinal_df=pd.DataFrame()
        try:
            df=pd.read_csv(r".\\"+self.output_filename)
        except:
            df=pd.DataFrame(columns=['Cidade', 'Unidade Lotérica', 'Quantidade de números apostados', 'Teimosinha', 'Tipo de Aposta', 'Cotas', 'Prêmio', 'Subject', 'Title'])
        # df['Cidade']=df

        unique_companies=self.input_df['Company Title'].unique()
        for uc in unique_companies:
            inner_df=self.input_df[self.input_df['Company Title'] == uc]
            for i in range(len(inner_df)):
                col_1=inner_df.iloc[i]['Cidade'].strip()
                col_2=inner_df.iloc[i]['Unidade Lotérica'].strip()

                if(uc == "Federal"):
                    try:
                        fdf=pd.read_csv("Testing_Federal.csv")
                    except:
                        fdf=pd.DataFrame(columns=['Destino', 'Bilhete', 'Valor do Prêmio (R$)', 'Unidade Lotérica', 'Cidade', 'Subject', 'Title'])
                    temp=fdf[(fdf['Cidade'] == col_1.strip()) & (fdf['Unidade Lotérica'] == col_2.strip()) & (fdf['Title'] == uc.strip())]
                    try:
                        ffinal_df=pd.concat([ffinal_df,temp])
                    except:
                        ffinal_df=pd.DataFrame(columns=['Destino', 'Bilhete', 'Valor do Prêmio (R$)', 'Unidade Lotérica', 'Cidade', 'Subject', 'Title'])
                else:
                    temp=df[(df['Cidade'] == col_1.strip()) & (df['Unidade Lotérica'] == col_2.strip()) & (df['Title'] == uc.strip())]
                    selected.append(temp)

        try:
            final_df=pd.concat(selected)
        except:
            final_df=pd.DataFrame(columns=['Cidade', 'Unidade Lotérica', 'Quantidade de números apostados', 'Teimosinha', 'Tipo de Aposta', 'Cotas', 'Prêmio', 'Subject', 'Title'])
        # df=df.drop_duplicates()

        # unique_selected=final_df['Title'].unique()

        for i in range(len(self.input_df)):
            title=self.input_df.iloc[i]['Company Title'].strip()
            col_1=self.input_df.iloc[i]['Cidade'].strip()
            col_2=self.input_df.iloc[i]['Unidade Lotérica'].strip()
            rep=self.input_df.iloc[i]['e-mail']

            if(title == "Federal"):
                found_df=ffinal_df[(ffinal_df['Title'] == title) & (ffinal_df['Cidade'] == col_1) & (ffinal_df['Unidade Lotérica'] == col_2)]
            else:
                found_df=final_df[(final_df['Title'] == title) & (final_df['Cidade'] == col_1) & (final_df['Unidade Lotérica'] == col_2)]
            if(len(found_df) != 0):
                subject=found_df.iloc[0]['Subject']
                try:
                    found_df=found_df.drop(['Title','Subject'],axis=1)
                except:
                    found_df=found_df.drop(['Title','Subject'],axis=1)
                resp=rep.split(",")
                for res in resp:
                    self.send_email(found_df,subject,res)


        # for us in unique_selected:
        #     dataframe=final_df[final_df['Title'] == us]
        #     subject=dataframe.iloc[0]['Subject']
        #     dataframe=dataframe.drop(['Title','Subject'],axis=1)
        #     self.send_email(dataframe,subject)

        final_df.to_csv(r".\\POST_"+self.output_filename,index=False)
        ffinal_df.to_csv("POST_"+"Testing_Federal.csv",index=False)
    

    def cleanup(self,name):
        name=name.replace("-","").replace(" ","").replace("_","")
        name=name.lower()
        name=name.replace(".aspx","")
        return name

    def parse(self,response):
        data=response.text
        data=json.loads(data)

        unquie_asin=self.input_df['Company Title'].unique()
        print(unquie_asin)
        # time.sleep(15)
        for record in data:
            if(record['titulo'] in unquie_asin):
                if(record['titulo'] in ['Federal']):
                    yield response.follow("https://servicebus2.caixa.gov.br/portaldeloterias/api/federal/",callback=self.single_page,meta={"modalidade":record['modalidade'],"titulo":record['titulo']})
                else:
                    name=self.cleanup(record['textoDoLink'])
                    print(name)
                    yield response.follow("https://servicebus2.caixa.gov.br/portaldeloterias/api/"+name,callback=self.get_total,meta={"modalidade":record['modalidade'],"titulo":record['titulo']})

    def single_page(self,response):
        model=response.meta.get('modalidade')
        title=response.meta.get('titulo')  
        subject="FEDERAL"
        # with open("Test.json","w") as w:
        #     w.write(str(response.body.decode()))
        j_data=json.loads(str(response.body.decode()))
        df=pd.DataFrame()
        rows=j_data['dezenasSorteadasOrdemSorteio']
        # print(len(rows))

        for i in range(len(rows)):
            df.at[i,'Destino']=i+1
            df.at[i,'Bilhete']=j_data['dezenasSorteadasOrdemSorteio'][i]
            # df.at[i,'Unidade Lotérica']=j_data['listaMunicipioUFGanhadores'][i]['nomeFatansiaUL']
            # df.at[i,'Cidade/UF']=j_data['listaMunicipioUFGanhadores'][i]['municipio']+"/"+j_data['listaMunicipioUFGanhadores'][i]['uf']
            df.at[i,'Valor do Prêmio (R$)']=j_data['listaRateioPremio'][i]['valorPremio']


            for temp in uni_cids:
                if(temp['posicao'] == i+1):
                    df.at[i,'Unidade Lotérica']=temp['nomeFatansiaUL']
                    # print("TEST",temp['municipio'].strip()+'/'+temp['uf'].strip())
                    df.at[i,'Cidade']=temp['municipio'].strip()+'/'+temp['uf'].strip()
                    # df.at[i,'Cidade']=df.iloc[i]['Cidade'].replace("-","/")
        # main_df=pd.concat(df)
        # main_df['Subject']=subject
        # main_df['Title']=title
        # print(df.head())
        subject=title+" - Concurso "+str(j_data['numero'])
        df['Subject']=subject
        df['Title']=title
        df.to_csv("Testing_Federal.csv",index=False)
        # main_df=df.to_json(orient='records')
        # # main_df=ast.literal_eval(main_df)
        # main_df=json.loads(main_df)
        
        # # main_df=json.loads(main_df)
        # # print("MAIN",main_df)
        # for record in main_df:
        #     # print("RECORD",record)
        #     yield dict(record)
        
        

    def get_total(self,response):
        model=response.meta.get('modalidade')
        title=response.meta.get('titulo')   
        # if(title in ):
            # subject="FEDERAL"
            # df=pd.read_html(response.body)
            # main_df=pd.concat(df)
            # main_df['Subject']=subject
            # main_df['Title']=title
            # main_df=main_df.to_json(orient='records')
            # main_df=json.loads(main_df)
            # for record in main_df:
            # # print(record)
            #     yield dict(record)
        # else:
        data=response.text
        data=json.loads(data)
        num=data['numero']
        yield response.follow(self.base_link.format(model,num),callback=self.final_scrape, meta={'title': title,'num':num})

        
    def final_scrape(self,response):
        num=response.meta.get('num')
        title=response.meta.get('title')
        subject=title+" - Concurso "+str(num)
        soup=BeautifulSoup(response.body,'html.parser')
        df=pd.read_html(response.body)
        main_df=pd.concat(df)
        main_df['Subject']=subject
        main_df['Title']=title
        main_df=main_df.to_json(orient='records')
        main_df=json.loads(main_df)
        # print(main_df)
        # print(type(main_df))
        # main_df=list(main_df)
        # yield None
        for record in main_df:
            # print(record)
            yield dict(record)
        # print(len(df))
        # print(df[1].head())
        # with open("test.html","a") as w:
        #     w.write(response.text)