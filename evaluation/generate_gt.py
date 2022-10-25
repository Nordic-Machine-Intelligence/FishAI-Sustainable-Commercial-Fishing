import pandas as pd
import numpy as np

#For day d, for fish f, find position (x,y) with largest catch

df = pd.read_csv("fangstdata_2022.csv",delimiter=";",decimal=",")


dates = ["10.10.2022","11.10.2022","12.10.2022","13.10.2022","14.10.2022","15.10.2022","16.10.2022","17.10.2022"]

fish = ["Berggylt","Makrell","Sild","Hyse","Sei","Uer (vanlig)","Lyr","Torsk","Breiflabb","Lange"]


res = {"Date":[],"Fish":[],"Lon":[],"Lat":[]}
for d in dates:
    for f in fish:
        curr = df[(df["Siste fangstdato"] == d) & (df["Art FAO"] == f)]
        if len(curr) == 0:
            #If no fish f on day d is caught
            print(d,f)
            continue
        a = curr.groupby(["Lat (lokasjon)","Lon (lokasjon)"])
        lat,lon = a["Produktvekt"].sum().idxmax()

        res["Date"].append(d)
        res["Fish"].append(f)
        res["Lat"].append(lat)
        res["Lon"].append(lon)

dg = pd.DataFrame(res)
dg.to_csv("gt.csv",sep=";")
