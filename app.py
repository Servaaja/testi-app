import os
import base64
from io import BytesIO
from flask import Flask, render_template, request, jsonify, after_this_request
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import matplotlib.gridspec as gridspec
import numpy as np
from datetime import datetime

app = Flask(__name__)


# Allow uploading files up to 16MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
print("Kohta 1")

# Home route
@app.route('/')
def home():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    print("Kohta 2")
    return render_template('index.html', timestamp=timestamp)
    

# Route to handle CSV file upload and return chart
@app.route('/upload', methods=['POST'])
def upload_file():
    print("Kohta 3")
    file = request.files['file']
    kiinteä_hinta_testi = request.form.get('number')
    print("Kohta 3.2")
    if file and file.filename.endswith('.csv'):
        # Save the uploaded file
        print("Kohta 4")
        filename = f"temp_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        file.save(filename)
        print("Kohta 5")

        #file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        #file.save(file_path)

        #Kun tämä on päällä näin niin homma toimii --------- The Agg backend is a non-interactive backend that does not require a GUI event loop
        plt.switch_backend('Agg')
        # Read the CSV with pandas
        try:
            print("Kohta 6")
            try:
                # Try to convert the value to a float
                kiinteä_hinta_testi = float(kiinteä_hinta_testi)
                print("Kohta 7")

            except ValueError:
                print("Kohta 8")
                return jsonify({'error': 'Invalid number format'}), 400


            print("Kohta 9")
            kulutusdata = pd.read_csv(filename,encoding = "ISO-8859-1", delimiter= ";", index_col=0)
            hintadata = pd.read_csv(r'https://raw.githubusercontent.com/Servaaja/testi-app/refs/heads/master/sahkon-hinta-010121-250125.csv', encoding = "ISO-8859-1", delimiter= ";", index_col=0)
            print("Kohta 10")


            hintadata = hintadata.dropna()
            #Resetoidaan indeksi - tarpeellinen juttu
            hintadata["Aika"] = hintadata.index
            hintadata.reset_index(drop=True, inplace=True)
            #konvertoidaan suomen formaatin päivämäärät yleiseen AIKAmuotoon
            hintadata['Aika'] = pd.to_datetime(hintadata['Aika'], format = "%d/%m/%Y %H.%M.%S")
            #konvertoidaan yleisesti käytetty muoto takaisin haluttuun muotoon - Jos tekee tän ei voi käyttää myöhemmin
            #hintadata['Aika'] = hintadata['Aika'].dt.strftime("%d/%m/%Y.%H.%M")
            #Pyöristä lähimpään ajat tuntiin
            hintadata['Aika'] = hintadata['Aika'].dt.round("H")

            #FINGRIDIN SIVUILTA KULUTUSDATA
            #Resetoidaan indeksi - tarpeellinen juttu
            kulutusdata.reset_index(drop=True, inplace=True)
            
            #Poistetaan turhat sarakkeet
            sarake_pois = ["Tuotteen tyyppi", "Yksikkötyyppi", "Lukeman tyyppi", "Laatu,", "Resoluutio"]
            kulutusdata = kulutusdata.drop([col for col in sarake_pois if col in kulutusdata.columns], axis=1)

            #Muutetaan data stringistä floatiksi, jotta voidaan resample.sum
            kulutusdata["Määrä"] = kulutusdata["Määrä"].str.replace(",", ".")
            kulutusdata["Määrä"] = kulutusdata["Määrä"].astype(float)
            
            #Konvertoidaan suomen formaatin päivämäärät yleiseen AIKAmuotoon -- FINGRIDN MUOTOON LAITA 2024-12-02T22:00:00Z
            kulutusdata['Alkuaika'] = pd.to_datetime(kulutusdata['Alkuaika'], format = "%Y-%m-%dT%H:%M:%SZ")
            
            #Pitää laittaa indeksiin kun resample toimii vain indeksillä
            kulutusdata.set_index('Alkuaika', inplace=True)
            #Tehdään resamplaus päivätasoo ja resetoidaan indeksi
            kulutusdata = kulutusdata.resample("H").sum().reset_index()
            
            kulutusdata = kulutusdata.rename(columns={"Alkuaika": "Aika", "Määrä": "Sähkönkulutus kWh"})




            int_year = 2024
    
            #globaali muuttuja
            global hintadata2023
            
            hintadata2023 = hintadata[hintadata["Aika"].dt.year == int_year]
            hintadata2023.reset_index(drop=True, inplace=True)                       

            #globaali muuttuja
            global taulukko2023
            
            #tehdään uusi taulukko yhdistellen aikaisempia
            taulukko2023 = hintadata2023.join(kulutusdata["Sähkönkulutus kWh"])

            #Vaihdetaan sarakkeiden paikkaa
            taulukko2023 = taulukko2023.reindex(sorted(taulukko2023.columns), axis=1)


            #Korvataan pilkut pisteillä, jotta voidaan operoida
            taulukko2023["Hinta (snt/kWh)"] = taulukko2023["Hinta (snt/kWh)"].str.replace(",", ".")
            #taulukko2023["Sähkönkulutus kWh"] = taulukko2023["Sähkönkulutus kWh"].str.replace(",", ".")

            #Muutetaan stringit floateiksi, jotta päästään kertolaskuun
            taulukko2023["Hinta (snt/kWh)"] = taulukko2023["Hinta (snt/kWh)"].astype(float)
            #taulukko2023["Sähkönkulutus kWh"] = taulukko2023["Sähkönkulutus kWh"].astype(float)

            #lasketaan uusi sarake taulukkoon
            taulukko2023["Hinta_X_Kulutus"] = taulukko2023["Hinta (snt/kWh)"] * taulukko2023["Sähkönkulutus kWh"]


            
            # Create a Seaborn plot (bar plot as an example)

            plt.figure(num=1,figsize=(20, 10))

            plt.plot(taulukko2023["Aika"], taulukko2023["Hinta (snt/kWh)"], linewidth = 0.5)
            #plt.fill_between(taulukko_pörssi["Aika"], taulukko_pörssi["Hinta_X_Kulutus"], alpha=0.7, color="darkred", linewidth=.09)
            #plt.ylim(bottom=0)

            kiinteä_hinta_sntKwh = kiinteä_hinta_testi 
            #8784 vaihtuu vuoden mukaan???
            y = np.full(len(taulukko2023), kiinteä_hinta_sntKwh)
            plt.plot(taulukko2023["Aika"], y)
            plt.grid(True)

            dates_for_ticks = pd.date_range(start=taulukko2023["Aika"].min(), end=taulukko2023["Aika"].max(), freq="M")
            plt.xticks(dates_for_ticks, fontsize=12)
            plt.xticks(rotation=45)

            plt.yticks(fontsize=12)

            plt.ylim(-20, 60)
            plt.ylabel("Hinta snt (€) / kWh", fontsize=15)

            plt.title("Pörssisähkön hintavaihtelu vuoden ajalta sekä kiinteä vertailuhinta", fontsize=20)

            print("Kohta 11")
            # Save the chart to a BytesIO buffer
            img1 = BytesIO()
            print("Kohta 11_1")
            plt.savefig(img1, format='png')
            plt.close()
            print("Kohta 11_2")
            img1.seek(0)
            print("Kohta 12")
            

            # Convert the image to base64 encoding
            img1_base64 = base64.b64encode(img1.getvalue()).decode('utf-8')
            img1_url = f"data:image/png;base64,{img1_base64}"
             

            #TOINEN KUVA TESTIÄ    
            kuvio = taulukko2023.pivot_table(values='Sähkönkulutus kWh', index=taulukko2023['Aika'].dt.month, columns=taulukko2023['Aika'].dt.hour, aggfunc='sum', fill_value=0)
            kuvio_max = kuvio.quantile(0.95).quantile(0.90)
            kuvio["kk-sum"] = kuvio.sum(axis = 1)
            kuvio.loc["tunti-sum"] = kuvio.sum(axis = 0)

            kuvio_arvot = kuvio.copy()
            kuvio_arvot["kk-sum"] = float('nan')
            kuvio_arvot["tunti-sum"] = float('nan')

            kuvio_summat = kuvio.copy()
            kuvio_summat.iloc[:-1, :-1] = float('nan')
              
            fig1 = plt.figure(num=2, figsize=(20, 10))
            print("TÄÄÄÄÄÄÄÄÄÄÄÄÄÄLLLLLLLLLLLÄÄÄÄÄÄÄÄÄÄÄ")  
            #annot = numerot näkyviin #rocket_r = käänteiset värit # fmt = desimaalit #vmin = minimiarvo
            sns.heatmap(kuvio_arvot, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax= kuvio_max)
            print("TÄÄÄÄÄÄÄÄÄÄÄÄÄÄLLLLLLLLLLLÄÄÄÄÄÄÄÄÄÄÄ")  
            sns.heatmap(kuvio_summat, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax=0, cbar=False)

            plt.title("Sähkönkulutus (kWh) kuukausittain ja tunneittain", fontsize = 14)
            plt.xlabel("Tunnit", fontsize = 14)
            plt.ylabel("Kuukaudet", fontsize = 14)
            plt.xticks(rotation=360)
            plt.yticks(rotation=360)


           
                
            img2 = BytesIO()
            plt.savefig(img2, format='png')

            plt.close(fig1)
            img2.seek(0)
 
            # Convert the image to base64 encoding
            img2_base64 = base64.b64encode(img2.getvalue()).decode('utf-8')
            img2_url = f"data:image/png;base64,{img2_base64}"



            #------------------------------MONEN KUVAN PAKETTI-------------------------------------------

            #-----------------KUVA 1---------------------
            pörssi_yö = taulukko2023[(taulukko2023['Aika'].dt.hour >= 22) | (taulukko2023['Aika'].dt.hour < 7)]
            pörssi_yö_KA = pörssi_yö["Hinta (snt/kWh)"].mean().round(3)
            pörssi_yö_MED = pörssi_yö["Hinta (snt/kWh)"].median()

            pörssi_päivä = taulukko2023[(taulukko2023['Aika'].dt.hour >= 7) & (taulukko2023['Aika'].dt.hour < 22)]
            pörssi_päivä_KA = pörssi_päivä["Hinta (snt/kWh)"].mean().round(3)
            pörssi_päivä_MED = pörssi_päivä["Hinta (snt/kWh)"].median()


            data = [[pörssi_yö_KA], [pörssi_päivä_KA]]
            columns = ['Keskiarvo']
            index = ['Yö 22-7', 'Päivä 7-22']

            pörssi_yö_päivä_taulukko =  pd.DataFrame(data, columns=columns, index=index)
            pörssi_yö_päivä_taulukko

            plt.figure(figsize=(3,3))
            plt.title("Pörssisähkön Yö- ja \n Päivähintojen (kWh/snt)", fontsize = 16)

            ax = sns.heatmap(pörssi_yö_päivä_taulukko, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False, annot_kws={"size": 30})
            ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize = 14)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0, fontsize = 14)

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(5)

            plt.savefig("kuva3.png", format='png',bbox_inches='tight', pad_inches=0.1)
            plt.close()

        

            #-----------------------KUVA 2 ------------------------------
            pörssisähkö_kk_taulukko = taulukko2023.copy()
            pörssisähkö_kk_taulukko ["Kuukausi"] = pörssisähkö_kk_taulukko["Aika"].dt.month
            pörssisähkö_kk_taulukko_2 = pörssisähkö_kk_taulukko.groupby(["Kuukausi"], as_index=False)["Hinta (snt/kWh)"].mean().round(2)


            data = [pörssisähkö_kk_taulukko_2]
            columns = ['Keskiarvo']
            kuukaudet = ['Tammi', "Helmi", "Maalis", "Huhti", "Touko", "Kesä", "Heinä", "Elo", "Syys", "Loka", "Marras", "Joulu" ]
            pörssisähkö_kk_taulukko_2 ["Kuukaudet"] = kuukaudet

            pörssisähkö_kk_taulukko_2.drop(columns=["Kuukausi"], inplace=True)
            pörssisähkö_kk_taulukko_2.set_index("Kuukaudet", inplace=True)
            pörssisähkö_kk_taulukko_2



            plt.figure(figsize=(1, 4))
            plt.title("Pörssisähkön kuukausittaiset keskihinnat")

            ax = sns.heatmap(pörssisähkö_kk_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False)
            ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(4)

            plt.savefig("kuva1_1", format='png')
            plt.close()


            #-----------------------KUVA 3----------------------------
            pörssisähkö_tunti_taulukko = taulukko2023.copy()
            pörssisähkö_tunti_taulukko ["Tunti"] = pörssisähkö_tunti_taulukko["Aika"].dt.hour
            pörssisähkö_tunti_taulukko_2 = pörssisähkö_tunti_taulukko.groupby(["Tunti"], as_index=False)["Hinta (snt/kWh)"].mean().round(2)


            #pörssisähkö_tunti_taulukko_2.drop(columns=["Tunti"], inplace=True)
            pörssisähkö_tunti_taulukko_2 = pörssisähkö_tunti_taulukko_2.pivot_table(columns = "Tunti", values = "Hinta (snt/kWh)")



            plt.figure(figsize=(12, 1))
            plt.title("Pörssisähkön keskihinnat tunneittain")

            ax = sns.heatmap(pörssisähkö_tunti_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False)
            ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            #ax.set_ylabel("")
            ax.set_xlabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(5)

            plt.savefig("kuva1_2", format='png')    
            plt.close()
            
            #---------------------KUVA 4---------------------
            pörssisähkö_viikonpäivä_taulukko = taulukko2023.copy()
            pörssisähkö_viikonpäivä_taulukko ["Viikonpäivä"] = pörssisähkö_viikonpäivä_taulukko["Aika"].dt.weekday
            pörssisähkö_viikonpäivä_taulukko_2 = pörssisähkö_viikonpäivä_taulukko.groupby(["Viikonpäivä"], as_index=False)["Hinta (snt/kWh)"].mean().round(2)


            data = [pörssisähkö_viikonpäivä_taulukko_2]
            columns = ['Keskiarvo']
            viikonpäivät = ['Ma', "Ti", "Ke", "To", "Pe", "La", "Su"]
            pörssisähkö_viikonpäivä_taulukko_2 ["Viikonpäivät"] = viikonpäivät

            pörssisähkö_viikonpäivä_taulukko_2.drop(columns=["Viikonpäivä"], inplace=True)
            pörssisähkö_viikonpäivä_taulukko_2.set_index("Viikonpäivät", inplace=True)
            pörssisähkö_viikonpäivä_taulukko_2



            plt.figure(figsize=(1, 4))
            plt.title("Pörssisähkön keskihinnat viikonpäivittäin")

            ax = sns.heatmap(pörssisähkö_viikonpäivä_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False)
            ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(4)

            plt.savefig("kuva1_3", format='png')
            plt.close()



            #---------------------KUVA 5--------------------------------
            pörssisähkö_vuosi_taulukko = taulukko2023.copy()
            pörssisähkö_vuosi_taulukko ["Vuosi"] = pörssisähkö_vuosi_taulukko["Aika"].dt.year
            pörssisähkö_vuosi_taulukko_2 = pörssisähkö_vuosi_taulukko.groupby(["Vuosi"], as_index=False)["Hinta (snt/kWh)"].mean().round(2)


            pörssisähkö_vuosi_taulukko_2.drop(columns=["Vuosi"], inplace=True)
            print("111")
            plt.figure(figsize=(2, 2))
            print("112")
            print("1122")
            plt.title("Pörssisähkön keskihinta - Vuosi")
            plt.tick_params(axis='y', length=0, labelleft=False, labelbottom=False)


            ax = sns.heatmap(pörssisähkö_vuosi_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False, annot_kws={"size": 20})
            ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(4)

            plt.savefig("kuva1_4", format='png')
            plt.close()

            print("1123")


            img11 = mpimg.imread("kuva1_1.png")
            img22 = mpimg.imread("kuva1_3.png")
            img33 = mpimg.imread("kuva1_4.png")
            img44 = mpimg.imread("kuva3.png")
            img55 = mpimg.imread("kuva1_2.png")

            # Create a 4x4 GridSpec
            fig = plt.figure(num=69, figsize=(20, 20))
            gs = gridspec.GridSpec(4, 2, figure=fig)
            print("1124")
            # Place the first image in the top-left 2x2 block (spans rows 0-1, cols 0-1)
            ax1 = fig.add_subplot(gs[0:2, 0:1])  # 2x2 block
            ax1.imshow(img11)
            ax1.set_title("Figure 1")
            ax1.axis('off')  # Hide axis

            # Place the second image in the top-right 2x2 block (spans rows 0-1, cols 2-3)
            ax2 = fig.add_subplot(gs[0:2, 1:2])  # 2x2 block
            ax2.imshow(img22)
            ax2.set_title("Figure 2")
            ax2.axis('off')

            # Place the third image in the bottom-left 2x2 block (spans rows 2-3, cols 0-1)
            ax3 = fig.add_subplot(gs[2:3, 0:1])  # 2x2 block
            ax3.imshow(img33)
            ax3.set_title("Figure 3")
            ax3.axis('off')

            # Place the fourth image in the bottom-right 2x2 block (spans rows 2-3, cols 2-3)
            ax4 = fig.add_subplot(gs[2:3, 1:2])  # 2x2 block
            ax4.imshow(img44)
            ax4.set_title("Figure 4")
            ax4.axis('off')

            # Place the fourth image in the bottom-right 2x2 block (spans rows 2-3, cols 2-3)
            ax5 = fig.add_subplot(gs[3, 0:2])  # 2x2 block
            ax5.imshow(img55)
            ax5.set_title("Figure 5")
            ax5.axis('off')


            img3 = BytesIO()
            plt.savefig(img3, format='png')
            plt.close()
            img3.seek(0)

            # Convert the image to base64 encoding
            img3_base64 = base64.b64encode(img3.getvalue()).decode('utf-8')
            img3_url = f"data:image/png;base64,{img3_base64}"

            

            print("113")

            #------------------------------MONEN KUVAN PAKETTI----------TOINEN SETTI------------------------------

            #-----------------------------KUVA 6-----------------------
            kulutus_kk_taulukko = taulukko2023.copy()
            kulutus_kk_taulukko ["Kuukausi"] = pörssisähkö_kk_taulukko["Aika"].dt.month
            kulutus_kk_taulukko_2 = kulutus_kk_taulukko.groupby(["Kuukausi"], as_index=False)["Sähkönkulutus kWh"].sum()


            data = [pörssisähkö_kk_taulukko_2]
            columns = ['Kulutus kWh']
            kuukaudet = ['Tammi', "Helmi", "Maalis", "Huhti", "Touko", "Kesä", "Heinä", "Elo", "Syys", "Loka", "Marras", "Joulu" ]
            kulutus_kk_taulukko_2 ["Kuukaudet"] = kuukaudet

            kulutus_kk_taulukko_2.drop(columns=["Kuukausi"], inplace=True)
            kulutus_kk_taulukko_2.set_index("Kuukaudet", inplace=True)
            kulutus_kk_taulukko_2



            plt.figure(figsize=(1, 4))
            plt.title("Sähkönkulutus kuukausittain")

            ax = sns.heatmap(kulutus_kk_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False)
            ax.xaxis.tick_top()
            ax.set_xticklabels(labels=["kWh"], rotation=0)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(4)

            #C:\Users\TeemunKone
            plt.savefig('kuva2_2', bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #------------------------KUVA 7----------------------------------
            kulutus_viikonpäivä_taulukko = taulukko2023.copy()
            kulutus_viikonpäivä_taulukko ["Viikonpäivä"] = kulutus_viikonpäivä_taulukko["Aika"].dt.weekday
            kulutus_viikonpäivä_taulukko_2 = kulutus_viikonpäivä_taulukko.groupby(["Viikonpäivä"], as_index=False)["Sähkönkulutus kWh"].sum()


            data = [kulutus_viikonpäivä_taulukko_2]
            columns = ['Kulutus']
            viikonpäivät = ['Ma', "Ti", "Ke", "To", "Pe", "La", "Su"]
            kulutus_viikonpäivä_taulukko_2 ["Viikonpäivät"] = viikonpäivät

            kulutus_viikonpäivä_taulukko_2.drop(columns=["Viikonpäivä"], inplace=True)
            kulutus_viikonpäivä_taulukko_2.set_index("Viikonpäivät", inplace=True)
            kulutus_viikonpäivä_taulukko_2



            plt.figure(figsize=(1, 4))
            plt.title("Sähkönkulutus viikonpäivittäin")

            ax = sns.heatmap(kulutus_viikonpäivä_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False)
            ax.xaxis.tick_top()
            ax.set_xticklabels(labels=["kWh"], rotation=0)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(4)


            plt.savefig('kuva2_3', bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #------------------------------KUVA 8----------------------------------------
            kulutus_tunti_taulukko = taulukko2023.copy()
            kulutus_tunti_taulukko ["Tunti"] = kulutus_tunti_taulukko["Aika"].dt.hour
            kulutus_tunti_taulukko_2 = kulutus_tunti_taulukko.groupby(["Tunti"], as_index=False)["Sähkönkulutus kWh"].sum()


            #pörssisähkö_tunti_taulukko_2.drop(columns=["Tunti"], inplace=True)
            kulutus_tunti_taulukko_2 = kulutus_tunti_taulukko_2.pivot_table(columns = "Tunti", values = "Sähkönkulutus kWh")



            plt.figure(figsize=(12, 1))
            plt.title("Sähkönkulutus tunneittain")

            ax = sns.heatmap(kulutus_tunti_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".0f", cbar=False)
            ax.xaxis.tick_top()
            ax.set_yticklabels(labels=["kWh"], rotation=0)
            ax.set_xlabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(5)

            plt.savefig('kuva2_4', bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #--------------------------------KUVA 9---------------------------------
            kulutus_vuosi_taulukko = taulukko2023.copy()
            kulutus_vuosi_taulukko ["Vuosi"] = kulutus_vuosi_taulukko["Aika"].dt.year
            kulutus_vuosi_taulukko_2 = kulutus_vuosi_taulukko.groupby(["Vuosi"], as_index=False)["Sähkönkulutus kWh"].sum()


            kulutus_vuosi_taulukko_2.drop(columns=["Vuosi"], inplace=True)

            plt.figure(figsize=(2, 2))
            plt.title("Sähkönkulutus vuodessa")
            plt.tick_params(axis='y', length=0, labelleft=False, labelbottom=False)


            ax = sns.heatmap(kulutus_vuosi_taulukko_2, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False, annot_kws={"size": 20})
            ax.xaxis.tick_top()
            ax.set_xticklabels(labels=["kWh"], rotation=0)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(3)

            plt.savefig('kuva2_1',  bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #---------------------------------KUVA 10-------------------------------------
            yökulutus = pörssi_yö["Sähkönkulutus kWh"].sum()
            päiväkulutus = pörssi_päivä["Sähkönkulutus kWh"].sum()


            plt.figure(figsize=(5, 4))
            plt.title("Sähkönkulutus yöllä ja päivällä (kWh)")
            data = [yökulutus, päiväkulutus]


            colors = [(0.31,0.608,0.796), (0.745,0.847,0.925),]

            plt.pie(data, labels = ["Yöllä", "Päivällä"], textprops={'fontsize': 14},colors=colors, explode= (0, 0.1), autopct=lambda p: f'{p:.1f}% ({int(p/100.*sum(data))} kWh)')

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(4)

            plt.savefig('kuva4')
            plt.close()


            img6 = mpimg.imread('kuva2_2.png')
            img7 = mpimg.imread('kuva2_3.png')
            img8 = mpimg.imread('kuva2_1.png')
            img9 = mpimg.imread('kuva4.png')
            img10 = mpimg.imread('kuva2_4.png')

            # Create a 4x4 GridSpec
            fig = plt.figure(num=79, figsize=(20, 20))
            gs = gridspec.GridSpec(4, 2, figure=fig)

            # Place the first image in the top-left 2x2 block (spans rows 0-1, cols 0-1)
            ax6 = fig.add_subplot(gs[0:2, 0:1])  # 2x2 block
            ax6.imshow(img6)
            ax6.set_title("Figure 1")
            ax6.axis('off')  # Hide axis

            # Place the second image in the top-right 2x2 block (spans rows 0-1, cols 2-3)
            ax7 = fig.add_subplot(gs[0:2, 1:2])  # 2x2 block
            ax7.imshow(img7)
            ax7.set_title("Figure 2")
            ax7.axis('off')

            # Place the third image in the bottom-left 2x2 block (spans rows 2-3, cols 0-1)
            ax8 = fig.add_subplot(gs[2:3, 0:1])  # 2x2 block
            ax8.imshow(img8)
            ax8.set_title("Figure 3")
            ax8.axis('off')

            # Place the fourth image in the bottom-right 2x2 block (spans rows 2-3, cols 2-3)
            ax9 = fig.add_subplot(gs[2:3, 1:2])  # 2x2 block
            ax9.imshow(img9)
            ax9.set_title("Figure 4")
            ax9.axis('off')

            # Place the fourth image in the bottom-right 2x2 block (spans rows 2-3, cols 2-3)
            ax10 = fig.add_subplot(gs[3, 0:2])  # 2x2 block
            ax10.imshow(img10)
            ax10.set_title("Figure 5")
            ax10.axis('off')


            # Adjust layout for better spacing
            #plt.tight_layout()


            img4 = BytesIO()
            plt.savefig(img4, format='png')
            plt.close()
            img4.seek(0)

            # Convert the image to base64 encoding
            img4_base64 = base64.b64encode(img4.getvalue()).decode('utf-8')
            img4_url = f"data:image/png;base64,{img4_base64}"

            print("114")
            
            #------------------------------MONEN KUVAN PAKETTI----------KOLMAS SETTI------------------------------

            #-----------------------------KUVA 11-----------------------
            plt.figure(figsize=(2, 2))
            plt.title("Kiinteä vertailuhinta \n € snt / kWh", fontsize = 10)
            plt.tick_params(axis='y', length=0, labelleft=False, labelbottom=False)


            #data = np.array([[10]])
            data = np.array([[kiinteä_hinta_sntKwh]])

            ax = sns.heatmap(data, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False, annot_kws={"size": 20})
            #ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            plt.xticks([])

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(3)

            for text in ax.texts:  # Loop through all annotation texts
                # Add " units" after each annotation value
                text.set_text(f'{text.get_text()} \n € snt  ')

            #C:\Users\TeemunKone
            plt.savefig('kuva3_1', bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #-----------------------------KUVA 12-----------------------
            hintataulukko = taulukko2023.copy()
            hintataulukko ["Kiinteä hinta (snt/kWh)"] = kiinteä_hinta_sntKwh
            hintataulukko ["Hinta_X_Kulutus_kiinteä"] = hintataulukko ["Sähkönkulutus kWh"] * hintataulukko ["Kiinteä hinta (snt/kWh)"]
            hintataulukko

            hinta_pörssi = hintataulukko.groupby(hintataulukko['Aika'].dt.year)['Hinta_X_Kulutus'].sum()
            hinta_kiinteä = hintataulukko.groupby(hintataulukko['Aika'].dt.year)['Hinta_X_Kulutus_kiinteä'].sum()

            data = np.array([[hinta_pörssi.iloc[0]]])

            plt.figure(figsize=(4, 4))

            ax = sns.heatmap(data/100, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False, annot_kws={"size": 40})
            #ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            plt.xticks([])
            plt.yticks([])

            plt.title("Sähköstä maksettu hinta € \n pörssihinnalla", fontsize = 24)

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(8)

            for text in ax.texts:  # Loop through all annotation texts
                # Add " units" after each annotation value
                text.set_text(f'{text.get_text()} €  ')

            #C:\Users\TeemunKone
            plt.savefig('kuva3_2', bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #-----------------------------KUVA 13-----------------------
            data = np.array([[hinta_kiinteä.iloc[0]]])

            plt.figure(figsize=(4, 4))

            ax = sns.heatmap(data/100, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False, annot_kws={"size": 40})
            #ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")


            plt.xticks([])
            plt.yticks([])

            plt.title("Sähköstä maksettu hinta € \n kiinteällä hinnalla", fontsize = 24)

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(8)

            for text in ax.texts:  # Loop through all annotation texts
                # Add " units" after each annotation value
                text.set_text(f'{text.get_text()} €  ')

            #C:\Users\TeemunKone
            plt.savefig('kuva3_3', bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #-----------------------------KUVA 14-----------------------
            data = np.array([[hinta_kiinteä.iloc[0] - hinta_pörssi.iloc[0]]])

            plt.figure(figsize=(3, 2))

            ax = sns.heatmap(data/100, annot=True, cmap="Blues", linewidths=2, linecolor="black", fmt=".2f", cbar=False, annot_kws={"size": 30})
            #ax.xaxis.tick_top()
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
            ax.set_ylabel("")

            plt.xticks([])
            plt.yticks([])

            plt.title(" Kiinteän hinnan ja \n pörssihinnan erotus \n (Kiinteä hinta - pörssihinta)")

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(3)

            for text in ax.texts:  # Loop through all annotation texts
                # Add " units" after each annotation value
                text.set_text(f'{text.get_text()} € ')

            #C:\Users\TeemunKone
            plt.savefig('kuva3_4', bbox_inches='tight', pad_inches=0.1)
            plt.close()

            #-----------------------------KUVA 15-----------------------
            yömaksu = pörssi_yö["Hinta_X_Kulutus"].sum() / 100 #Muutetaan euroiksi
            päivämaksu = pörssi_päivä["Hinta_X_Kulutus"].sum() / 100 #Muutetaan euroiksi


            plt.figure(figsize=(5, 4))
            plt.title("Yö- ja päiväsähköstä maksettu vuodessa €")
            data = [yömaksu, päivämaksu]

            cmap = plt.get_cmap("Blues")
            colors = [(0.31,0.608,0.796), (0.745,0.847,0.925),]

            plt.pie(data, labels = ["Yö", "Päivä"], colors=colors,textprops={'fontsize': 14}, explode= (0, 0.1), autopct=lambda p: f'{p:.1f}% ({float(p/100.*sum(data)):.2f} €)')

            fig = plt.gcf()
            fig.patch.set_edgecolor('black')
            fig.patch.set_linewidth(5)

            #C:\Users\TeemunKone
            plt.savefig('kuva5')
            plt.close()


            img11 = mpimg.imread('kuva3_2.png')
            img12 = mpimg.imread('kuva3_3.png')
            img13 = mpimg.imread('kuva3_1.png')
            img14 = mpimg.imread('kuva3_4.png')
            img15 = mpimg.imread('kuva5.png')

            # Create a 4x4 GridSpec
            fig = plt.figure(num=89, figsize=(10, 20))
            gs = gridspec.GridSpec(4, 2, figure=fig)

            # Place the first image in the top-left 2x2 block (spans rows 0-1, cols 0-1)
            ax11 = fig.add_subplot(gs[0:1, 0:1])  # 2x2 block
            ax11.imshow(img11)
            ax11.set_title("Figure 1")
            ax11.axis('off')  # Hide axis

            # Place the second image in the top-right 2x2 block (spans rows 0-1, cols 2-3)
            ax12 = fig.add_subplot(gs[0:1, 1:2])  # 2x2 block
            ax12.imshow(img12)
            ax12.set_title("Figure 2")
            ax12.axis('off')

            # Place the third image in the bottom-left 2x2 block (spans rows 2-3, cols 0-1)
            ax13 = fig.add_subplot(gs[1:2, 0:1])  # 2x2 block
            ax13.imshow(img13)
            ax13.set_title("Figure 3")
            ax13.axis('off')

            # Place the fourth image in the bottom-right 2x2 block (spans rows 2-3, cols 2-3)
            ax14 = fig.add_subplot(gs[1:2, 1:2])  # 2x2 block
            ax14.imshow(img14)
            ax14.set_title("Figure 4")
            ax14.axis('off')

            # Place the fourth image in the bottom-right 2x2 block (spans rows 2-3, cols 2-3)
            ax15 = fig.add_subplot(gs[2:4, 0:2])  # 2x2 block
            ax15.imshow(img15)
            ax15.set_title("Figure 5")
            ax15.axis('off')


            # Adjust layout for better spacing
            plt.tight_layout()

            img5 = BytesIO()
            plt.savefig(img5, format='png')
            plt.close()   
            img5.seek(0)

            # Convert the image to base64 encoding
            img5_base64 = base64.b64encode(img5.getvalue()).decode('utf-8')
            img5_url = f"data:image/png;base64,{img5_base64}"


            print("115")

            #-------------------Kulutuksen jakautuminen Heatmap - Kuukaudet ja Tunnit------------------------
            kuvio = taulukko2023.pivot_table(values='Sähkönkulutus kWh', index=taulukko2023['Aika'].dt.month, columns=taulukko2023['Aika'].dt.hour, aggfunc='sum', fill_value=0)
            kuvio_max = kuvio.quantile(0.95).quantile(0.90)
            kuvio["kk-sum"] = kuvio.sum(axis = 1)
            kuvio.loc["tunti-sum"] = kuvio.sum(axis = 0)

            kuvio_arvot = kuvio.copy()
            kuvio_arvot["kk-sum"] = float('nan')
            kuvio_arvot["tunti-sum"] = float('nan')

            kuvio_summat = kuvio.copy()
            kuvio_summat.iloc[:-1, :-1] = float('nan')

            plt.figure(figsize=(20, 10))

            #annot = numerot näkyviin #rocket_r = käänteiset värit # fmt = desimaalit #vmin = minimiarvo
            sns.heatmap(kuvio_arvot, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax= kuvio_max)
            sns.heatmap(kuvio_summat, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax=0, cbar=False)

            plt.title("Sähkönkulutus (kWh) kuukausittain ja tunneittain", fontsize = 14)
            plt.xlabel("Tunnit", fontsize = 14)
            plt.ylabel("Kuukaudet", fontsize = 14)
            plt.xticks(rotation=360)
            plt.yticks(rotation=360)

            #C:\Users\TeemunKone
            #plt.savefig('kuva6')

            img6 = BytesIO()
            plt.savefig(img6, format='png')
            plt.close()
            img6.seek(0)

            # Convert the image to base64 encoding
            img6_base64 = base64.b64encode(img6.getvalue()).decode('utf-8')
            img6_url = f"data:image/png;base64,{img6_base64}"

            print("116")
            #---------------------------Kulutuksen jakautuminen Heatmap - Kuukaudet ja Päivät------------------------
            kuvio2 = taulukko2023.pivot_table(values='Sähkönkulutus kWh', index=taulukko2023['Aika'].dt.month, columns=taulukko2023['Aika'].dt.day, aggfunc='sum', fill_value=0)
            kuvio2_max = kuvio2.quantile(0.95).quantile(0.90)
            kuvio2_min = kuvio2.quantile(0.05).quantile(0.10)
            kuvio2["kk-sum"] = kuvio2.sum(axis = 1)
            kuvio2.loc["päivä-sum"] = kuvio2.sum(axis = 0)

            kuvio2_arvot = kuvio2.copy()
            kuvio2_arvot["kk-sum"] = float('nan')
            kuvio2_arvot["päivä-sum"] = float('nan')

            kuvio2_summat = kuvio2.copy()
            kuvio2_summat.iloc[:-1, :-1] = float('nan')

            plt.figure(figsize=(25, 10))

            #annot = numerot näkyviin #rocket_r = käänteiset värit # fmt = desimaalit #vmin = minimiarvo
            sns.heatmap(kuvio2_arvot, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=kuvio2_min, vmax=kuvio2_max)
            sns.heatmap(kuvio2_summat, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax=0, cbar=False)

            plt.title("Sähkönkulutus (kWh) kuukausittain ja päivittäin", fontsize = 14)
            plt.xlabel("Päivät", fontsize = 14)
            plt.ylabel("Kuukaudet", fontsize = 14)
            plt.xticks(rotation=360)
            plt.yticks(rotation=360)


            #C:\Users\TeemunKone
            #plt.savefig('kuva7')

            img7 = BytesIO()
            plt.savefig(img7, format='png')
            plt.close()
            img7.seek(0)

            # Convert the image to base64 encoding
            img7_base64 = base64.b64encode(img7.getvalue()).decode('utf-8')
            img7_url = f"data:image/png;base64,{img7_base64}"

            #---------------------------------Sähköstä maksetun hinnan jakautuminen Heatmap - Kuukaudet ja Tunnit--------------------
            kuvio3 = taulukko2023.pivot_table(values='Hinta_X_Kulutus', index=taulukko2023['Aika'].dt.month, columns=taulukko2023['Aika'].dt.hour, aggfunc='sum', fill_value=0)
            kuvio3_max = kuvio3.quantile(0.95).quantile(0.90)
            kuvio3["kk-sum"] = kuvio3.sum(axis = 1)
            kuvio3.loc["tunti-sum"] = kuvio3.sum(axis = 0)

            kuvio3_arvot = kuvio3.copy()
            kuvio3_arvot["kk-sum"] = float('nan')
            kuvio3_arvot["tunti-sum"] = float('nan')

            kuvio3_summat = kuvio3.copy()
            kuvio3_summat.iloc[:-1, :-1] = float('nan')


            plt.figure(figsize=(20, 10))

            #annot = numerot näkyviin #rocket_r = käänteiset värit # fmt = desimaalit #vmin = minimiarvo
            sns.heatmap(kuvio3_arvot / 100, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax=kuvio3_max/100)
            sns.heatmap(kuvio3_summat / 100, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax=0, cbar=False)

            plt.title("Sähköstä maksettu hinta € (pörssisähkö) kuukausittain ja tunneittain", fontsize = 14)
            plt.xlabel("Tunnit", fontsize = 14)
            plt.ylabel("Kuukaudet", fontsize = 14)
            plt.xticks(rotation=360)
            plt.yticks(rotation=360)

            #C:\Users\TeemunKone
            #plt.savefig('kuva8')


            img8 = BytesIO()
            plt.savefig(img8, format='png')
            plt.close()
            img8.seek(0)

            # Convert the image to base64 encoding
            img8_base64 = base64.b64encode(img8.getvalue()).decode('utf-8')
            img8_url = f"data:image/png;base64,{img8_base64}"

            #---------------------------------Sähköstä maksetun hinnan jakautuminen Heatmap - Kuukaudet ja Päivät------------------------
            kuvio4 = taulukko2023.pivot_table(values='Hinta_X_Kulutus', index=taulukko2023['Aika'].dt.month, columns=taulukko2023['Aika'].dt.day, aggfunc='sum', fill_value=0)
            kuvio4_max = kuvio4.quantile(0.95).quantile(0.90)
            kuvio4["kk-sum"] = kuvio4.sum(axis = 1)
            kuvio4.loc["tunti-sum"] = kuvio4.sum(axis = 0)

            kuvio4_arvot = kuvio4.copy()
            kuvio4_arvot["kk-sum"] = float('nan')
            kuvio4_arvot["tunti-sum"] = float('nan')

            kuvio4_summat = kuvio4.copy()
            kuvio4_summat.iloc[:-1, :-1] = float('nan')

            plt.figure(figsize=(20, 10))

            #annot = numerot näkyviin #rocket_r = käänteiset värit # fmt = desimaalit #vmin = minimiarvo
            sns.heatmap(kuvio4_arvot / 100, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax=kuvio4_max/100)
            sns.heatmap(kuvio4_summat / 100, annot=True, cmap="Blues", linewidths=.9, linecolor="black", fmt=".1f", vmin=0, vmax=0, cbar=False)

            plt.title("Sähköstä maksettu hinta € (pörssisähkö) kuukausittain ja päivittäin", fontsize = 14)
            plt.xlabel("Päivät", fontsize = 14)
            plt.ylabel("Kuukaudet", fontsize = 14)
            plt.xticks(rotation=360)
            plt.yticks(rotation=360)

            #C:\Users\TeemunKone
            #plt.savefig('kuva9')

            img9 = BytesIO()
            plt.savefig(img9, format='png')
            plt.close()
            img9.seek(0)

            # Convert the image to base64 encoding
            img9_base64 = base64.b64encode(img9.getvalue()).decode('utf-8')
            img9_url = f"data:image/png;base64,{img9_base64}"
            print("117")
            #--------------------Pörssi vs kiinteä heatmap Kuukausi ja Päivä - Mitä on maksettu sähköstä----------------------------------------
            taulukko_pörssi = taulukko2023.copy()
            #Pitää laittaa indeksiin kun resample toimii vain indeksillä
            taulukko_pörssi.set_index('Aika', inplace=True)
            #Tehdään resamplaus päivätasoo ja resetoidaan indeksi
            taulukko_pörssi = taulukko_pörssi.resample("D").sum().reset_index()

            taulukko_kiinteä = taulukko2023.copy()
            taulukko_kiinteä.drop(columns=["Hinta_X_Kulutus",'Hinta (snt/kWh)'], inplace=True)
            taulukko_kiinteä["Hinta kiinteä (snt/kWh)"] = kiinteä_hinta_sntKwh

            taulukko_kiinteä["Hinta_X_Kulutus"] = taulukko_kiinteä["Hinta kiinteä (snt/kWh)"] * taulukko_kiinteä["Sähkönkulutus kWh"]

            #Pitää laittaa indeksiin kun resample toimii vain indeksillä
            taulukko_kiinteä.set_index('Aika', inplace=True)
            #Tehdään resamplaus ja resetoidaan indeksi
            taulukko_kiinteä = taulukko_kiinteä.resample("D").sum().reset_index()

            taulukko_erotus = taulukko_pörssi.copy()
            taulukko_erotus ["Hinta_X_Kulutus_kiinteä"] = taulukko_kiinteä["Hinta_X_Kulutus"]
            taulukko_erotus ["Kiinteä - Pörssi"] = taulukko_erotus ["Hinta_X_Kulutus_kiinteä"] - taulukko_erotus ["Hinta_X_Kulutus"]

            kuvio5 = taulukko_erotus.pivot_table(values='Kiinteä - Pörssi', index=taulukko_erotus['Aika'].dt.month, columns=taulukko_erotus['Aika'].dt.day, aggfunc='sum', fill_value=0)
            kuvio5_max = kuvio5.quantile(0.95).quantile(0.90)
            kuvio5_min = kuvio5.quantile(0.05).quantile(0.1)

            #Kiinteä - Pörssi = jos positiivinen luku niin kiinteä ollut kalliimpi vaihtoehto

            plt.figure(figsize=(24, 10))

            cmap = sns.diverging_palette(10, 125, as_cmap=True)
            #annot = numerot näkyviin #rocket_r = käänteiset värit # fmt = desimaalit #vmin = minimiarvo
            sns.heatmap(kuvio5, annot=True, cmap=cmap, center = 0, linewidths=.9, linecolor="black", fmt=".0f", vmin=kuvio5_min , vmax=kuvio5_max)

            plt.title("Sähkösopimusten välinen hintaero (€ snt) kuukausittain ja päivittäin -- kiinteä - pörssi", fontsize=16)
            plt.xlabel("Päivät", fontsize=14)
            plt.ylabel("Kuukaudet", fontsize=14)
            plt.yticks(rotation=360)

            #C:\Users\TeemunKone
            #plt.savefig('kuva10')

            img10 = BytesIO()
            plt.savefig(img10, format='png')
            plt.close()
            img10.seek(0)

            # Convert the image to base64 encoding
            img10_base64 = base64.b64encode(img10.getvalue()).decode('utf-8')
            img10_url = f"data:image/png;base64,{img10_base64}"


            #--------------------------Pörssi vs kiinteä heatmap Kuukausi ja Tunti - Mitä on maksettu sähköstä--------------------------------
            taulukko_pörssi2 = taulukko2023.copy()

            #Pitää laittaa indeksiin kun resample toimii vain indeksillä
            taulukko_pörssi2.set_index('Aika', inplace=True)
            #Tehdään resamplaus päivätasoo ja resetoidaan indeksi
            taulukko_pörssi2 = taulukko_pörssi2.resample("H").sum().reset_index()


            taulukko_kiinteä2 = taulukko2023.copy()
            taulukko_kiinteä2.drop(columns=["Hinta_X_Kulutus",'Hinta (snt/kWh)'], inplace=True)
            taulukko_kiinteä2["Hinta kiinteä (snt/kWh)"] = kiinteä_hinta_sntKwh

            taulukko_kiinteä2["Hinta_X_Kulutus"] = taulukko_kiinteä2["Hinta kiinteä (snt/kWh)"] * taulukko_kiinteä2["Sähkönkulutus kWh"]

            #Pitää laittaa indeksiin kun resample toimii vain indeksillä
            taulukko_kiinteä2.set_index('Aika', inplace=True)
            #Tehdään resamplaus ja resetoidaan indeksi
            taulukko_kiinteä2 = taulukko_kiinteä2.resample("H").sum().reset_index()


            taulukko_erotus2 = taulukko_pörssi2.copy()
            taulukko_erotus2 ["Hinta_X_Kulutus_kiinteä"] = taulukko_kiinteä2["Hinta_X_Kulutus"]
            taulukko_erotus2 ["Kiinteä - Pörssi"] = taulukko_erotus2 ["Hinta_X_Kulutus_kiinteä"] - taulukko_erotus2 ["Hinta_X_Kulutus"]


            kuvio6 = taulukko_erotus2.pivot_table(values='Kiinteä - Pörssi', index=taulukko_erotus2['Aika'].dt.month, columns=taulukko_erotus2['Aika'].dt.hour, aggfunc='sum', fill_value=0)

            #Kiinteä - Pörssi = jos positiivinen luku niin kiinteä ollut kalliimpi vaihtoehto

            plt.figure(figsize=(24, 8))

            cmap = sns.diverging_palette(10, 125, as_cmap=True)
            #annot = numerot näkyviin #rocket_r = käänteiset värit # fmt = desimaalit #vmin = minimiarvo
            sns.heatmap(kuvio6, annot=True, cmap=cmap, center = 0, linewidths=.9, linecolor="black", fmt=".0f", vmax=70, vmin=-40)

            plt.title("Sähkösopimusten välinen hintaero (€ snt) kuukausittain ja tunneittain -- kiinteä - pörssi", fontsize=14)
            plt.xlabel("Tunnit", fontsize=14)
            plt.ylabel("Kuukaudet", fontsize=14)

            #C:\Users\TeemunKone
            #plt.savefig('kuva11')

            img11 = BytesIO()
            plt.savefig(img11, format='png')
            plt.close()
            img11.seek(0)

            # Convert the image to base64 encoding
            img11_base64 = base64.b64encode(img11.getvalue()).decode('utf-8')
            img11_url = f"data:image/png;base64,{img11_base64}"
            print("118")
            #---------------------------Kiinteä vs Pörssi - Kumulatiivinen aikajana siitä kumman kanssa on ns. plussalla----------------------------------
            taulukko_kumSum = taulukko_erotus2.copy()
            #resetoidaan indeksi ja resampletaan ennen rivin laskemista, koska silloin kaikke menee oikein
            taulukko_kumSum.set_index('Aika', inplace=True)
            taulukko_kumSum = taulukko_kumSum.resample("D").sum().reset_index()
            taulukko_kumSum ["Kiinteä - Pörssi KumSum"] = taulukko_kumSum ["Kiinteä - Pörssi"].cumsum()

            plt.figure(figsize=(20, 10))

            # jaetaan 100 nii saadaan Eurot.
            # Positiivinen luku niin pörssisähkö on voitolla

            color=[(0,0.565,0.922)]
            plt.fill_between(taulukko_kumSum["Aika"], taulukko_kumSum ["Kiinteä - Pörssi KumSum"] / 100, alpha=0.7, color=color, linewidth=.09)

            #Start ja End vaihtelee vuosittain
            dates_for_ticks2 = pd.date_range(start="2023-12-31", end="2024-12-31", freq="M")
            plt.xticks(dates_for_ticks2)
            plt.xticks(rotation=360)
            plt.title("Kumulatiivinen hintaero kiinteän sähkön ja pörssisähkön välillä \n positiivinen luku niin pörssisähkö on halvempi", fontsize=14)
            plt.xlabel("Päivämäärä", fontsize=14)
            plt.ylabel("Euroa (€)", fontsize=14)
            plt.grid(True, color='black', linewidth=0.3)


            #C:\Users\TeemunKone
            #plt.savefig('kuva12')

            img12 = BytesIO()
            plt.savefig(img12, format='png')
            plt.close()
            img12.seek(0)

            # Convert the image to base64 encoding
            img12_base64 = base64.b64encode(img12.getvalue()).decode('utf-8')
            img12_url = f"data:image/png;base64,{img12_base64}"
                

            print("119")

            # Clean up after request
            @after_this_request
            def cleanup(response):
                img1.close()
                img2.close()
                img3.close()
                img4.close()
                img5.close()
                img6.close()
                img7.close()
                img8.close()
                img9.close()
                img10.close()
                img11.close()
                img12.close()
                if os.path.exists(file.filename):
                    os.remove(file.filename)
                return response


            print("LOPPU")


            return jsonify({
                'chart1': img1_url,
                'chart2': img2_url,
                'chart3': img3_url,
                'chart4': img4_url,
                'chart5': img5_url,
                'chart6': img6_url,
                'chart7': img7_url,
                'chart8': img8_url,
                'chart9': img9_url,
                'chart10': img10_url,
                'chart11': img11_url,
                'chart12': img12_url
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Only CSV files are allowed'}), 400


if __name__ == '__main__':
    app.run(debug=True)
