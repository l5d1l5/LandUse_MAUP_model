import arcpy, numpy, math
import os
import os.path
from numpy import *
from arcpy import env
import random
from arcpy.sa import *
import decimal


def liczenie_atrybutow(maup_kopia):
        inZoneData = maup_kopia
        zoneField = "ajdi"

        ## przerobic to zeby bylo w petli jak czlowiek
        pole = "przyd"
        pole2 = "przyd_rel"
        pole3 = "przyd_wo"
        pole4 = "prz_wo_rel"
        pole5 = "les_mod_po"
        pole6 = "nr_modelu"

        lista_pol = [pole, pole2, pole3, pole4, pole5]
        for pol in lista_pol:
            try:
                arcpy.AddField_management(maup_kopia, pol, "FLOAT")
            except:
                print "bla"

        arcpy.AddField_management(maup_kopia, pole6, "TEXT")

        nazwa_tabeli= "przydatnosc"
        outTable = folder_tabele + "\\" + nazwa_tabeli + ".dbf"
        outZSaT = arcpy.sa.ZonalStatisticsAsTable(inZoneData, zoneField, przydatnosc_lesna, outTable, "DATA", "MEAN")
        
        # Create a feature layer from the vegtype featureclass
        maup_lyr = "maup_lyr"
        arcpy.MakeFeatureLayer_management(maup_kopia,  maup_lyr)
        # Join the feature layer to a table
        arcpy.AddJoin_management(maup_lyr, "ajdi", outTable, "ajdi")
        # Populate the newly created field with values from the joined table
        arcpy.CalculateField_management(maup_lyr, pole, "!MEAN!", "PYTHON")
        arcpy.RemoveJoin_management(maup_lyr, "przydatnosc")

        fields = [pole, pole2]
        cursor = arcpy.UpdateCursor(maup_kopia, fields)
        for cur in cursor:
            przyd_relatywna = cur.getValue(pole)/przyd_mean
            cur.setValue(pole2, przyd_relatywna)
            cursor.updateRow(cur)

        # Process: Reclassify
        las01 = mapa_les_path + "\\reklas.tif"
        rastercalc = mapa_les_path + "\\las01_przyd.tif"
        arcpy.Reclassify_3d(las_rol, "Value", "0 1;1 0", las01, "DATA")
        outTimes = Times(las01, przydatnosc_lesna)
        outTimes.save(rastercalc)

        nazwa_tabeli= "przydatnosc_wo"
        outTable2 = folder_tabele + "\\" + nazwa_tabeli + ".dbf"
        outZSaT = arcpy.sa.ZonalStatisticsAsTable(inZoneData, zoneField, rastercalc, outTable2, "DATA", "MEAN")
        arcpy.AddJoin_management(maup_lyr, "ajdi", outTable2, "ajdi")
        # Populate the newly created field with values from the joined table
        arcpy.CalculateField_management (maup_lyr, pole3, "!MEAN!", "PYTHON")
        fields = [pole3, pole4]
        rast_przyd_wo = arcpy.Raster(rastercalc)

        ## parametry rastra przydatnosci
        przyd_wo_mean = rast_przyd_wo.mean
        cursor = arcpy.UpdateCursor(maup_kopia, fields)

        for cur in cursor:
            przyd_relatywna = cur.getValue(pole3)/przyd_wo_mean
            cur.setValue(pole4, przyd_relatywna)
            cursor.updateRow(cur)

        arcpy.RemoveJoin_management(maup_lyr, "przydatnosc_wo")
        raster_lesny = arcpy.Raster(las_rol)
        les_mod = raster_lesny.mean
        #les_mod = licz_procent(las_rol1)
        #arcpy.CalculateField_management (maup_lyr, pole5, les_mod, "PYTHON")
        fields = [pole, pole5]
        cursor = arcpy.UpdateCursor(maup_kopia, fields)
        for cur in cursor:
            cur.setValue(pole5, les_mod)
            cursor.updateRow(cur)

        nazwa_modelu2 = "kon_" + nazwa_modelu
        arcpy.CalculateField_management(maup_lyr, pole6, "'" + nazwa_modelu2 + "'", "PYTHON")

def licz_procent(las_rol1):
    global liczba_pikseli
    mapa_les=arcpy.NumPyArrayToRaster(las_rol1, pnt, cellSize, cellSize,  -2147483647)
    mapa_les_output = mapa_les_path + "\\" + str(nazwa_modelu) + "poczatek.tif"
    mapa_les.save(mapa_les_output)
    values = {}
    #arcpy.BuildRasterAttributeTable_management(mapa_les_output, "Overwrite")
    with arcpy.da.SearchCursor(mapa_les_output, ['VALUE', 'COUNT']) as rows:
        for row in rows:
          # wyswietlamy liczbe pikseli '1'
          values[row[0]] = row[1]
          liczba_lasu= values.get(1, 0)
          liczba_nielasu= values.get(0,0)
    liczba_pikseli = liczba_lasu + liczba_nielasu
    procentowa_les =liczba_lasu/liczba_pikseli
    return procentowa_les

def liczenie_lesistosci(mapa_les_output, pole_wynik):
        inZoneData = maup_kopia
        zoneField = "ajdi"
        inraster = mapa_les_output
        nazwa_tabeli = "lesistosc"
        outTable = folder_tabele + "\\" + nazwa_tabeli + ".dbf"
        outZSaT = arcpy.sa.ZonalStatisticsAsTable(inZoneData, zoneField, mapa_les_output, outTable, "DATA", "MEAN")
        iterator_w_tysiacach = iterator2/1000
        pole_wynik = pole_wynik
        maup_lyr = "maup_lyr"
        # Add the new field
        arcpy.AddField_management (maup_kopia, pole_wynik ,"FLOAT")
        # Create a feature layer from the vegtype featureclass
        arcpy.MakeFeatureLayer_management (maup_kopia,  maup_lyr)
        # Join the feature layer to a table
        arcpy.AddJoin_management(maup_lyr, "ajdi", outTable, "ajdi")
        # Populate the newly created field with values from the joined table
        arcpy.CalculateField_management(maup_lyr, pole_wynik, "!MEAN!", "PYTHON")
        arcpy.RemoveJoin_management(maup_lyr, "lesistosc")

def liczenie_mapy(las_rol1, iterator2, wejsciowa, liczba_lasu_docelowa, koniec):
    global liczba_lat
    global liczba_pikseli
    iterator_w_tysiacach = int(iterator2/1000)
    mapa_les = arcpy.NumPyArrayToRaster(las_rol1, pnt, cellSize, cellSize,  -2147483647)
    mapa_les_output = mapa_les_path + "\\" + str(nazwa_modelu) + "_" + str(iterator_w_tysiacach) + ".tif"
    mapa_les.save(mapa_les_output)

    if koniec == -1:
        liczenie_lesistosci(mapa_les, "wynik_pocz")

    if koniec == 1:
        print "robimy koncowa mape"
        liczenie_lesistosci(mapa_les, "wynik_konc")
            
    values = {}
    #arcpy.BuildRasterAttributeTable_management(mapa_les_output, "Overwrite")
    with arcpy.da.SearchCursor(mapa_les_output, ['VALUE', 'COUNT']) as rows:
        for row in rows:
            if row[1] > -10:
              values[row[0]] = row[1]
              liczba_lasu = values.get(1, 0)
              liczba_nielasu = values.get(0, 0)

    liczba_pikseli = liczba_lasu + liczba_nielasu
    procentowa_les =liczba_lasu / liczba_pikseli
    print "procentowa les " + str(procentowa_les)
    return liczba_lasu

## tu wstawimy funkcje ktora zwraca liczbe - wartosc sasiedztwa dla komorki
## oraz w przypadku True sprawdza, czy nie mamy dziur w okolicy i lata je
def licz_sasiedztwo(x1, y1, glebiej):
    prog_sasiedztwa = 0
    for i in range(-1, 2):
        for j in range(-1, 2):
            prog_sasiedztwa = prog_sasiedztwa + las_rol1[x1 + i, y1 + j]
            if glebiej == True:
                latacz_dziur = licz_sasiedztwo(x1 + i, y1 + j, False)
                if latacz_dziur > 7:
                    las_rol1[x1 + i, y1 + j] = 1
                    liczba_zal = liczba_zal + 1
            else:
                pass
    return prog_sasiedztwa

def licz_podatnosc(p1, prog_sasiedztwa):
    #ROZKMINIC JAK TO LUCZYC ZEBY BYLO PODOBNE DO DYNACLUE
    p1_wzgledne= p1/przyd_mean
    sasiedztwo_wzgledne = prog_sasiedztwa/7.0
    #0.4 wziete z dynaclue
    podatnosc =p1_wzgledne
    return podatnosc

#sprawdzic co to r2 - w tym wypadku to nic
#zamienic losowanie na wybor najbqrdziej przydatnej komorki -->> nastepnie sprawdzenie jej sasiedztwa. jak jest to zalesiamy
def losowanie(iterator2):
    x1 = 0
    y1 = 0
    kontrolka = 1
    iterator = 0
    global prog_sasiedztwa
    global liczba_zal
    prog_sasiedztwa = 0
    losowanie = 1

    while  losowanie ==1:
        global liczba_zal
         #  losujemy komorke rolna - ma miec wartosc '0' i musi sasiadowac z przynajmniej jedna komorka lesna (prog przynajmniej 2)
        x1 = random.randint(0, dlugosc)
        if x1>(dlugosc - 10):
            x1=dlugosc - random.randint(10, 100)

        y1 = random.randint(0, szerokosc)
        if y1>(szerokosc-10):
           y1=szerokosc - random.randint(10, 100)
        try:
            kontrolka = las_rol1[x1, y1]
        except:
            return
        prog_sasiedztwa= 0
        #  sprawdzamy sasiedztwo komorki rolnej - bo juz jest wylosowana rolna - 0
        if kontrolka == 0:
            prog_sasiedztwa = licz_sasiedztwo(x1, y1, False)
            if prog_sasiedztwa > 8:
                return
            elif prog_sasiedztwa > 7:
                las_rol1[x1, y1] = 1
                liczba_zal = liczba_zal +1
                #if zalesienie_dod ==1:
                # zalesianie_dodatkowej(x1,y1)
                losowanie = 0
                return
            elif prog_sasiedztwa > 1:
                 try:
                    P1 = przydatnosc1[x1, y1]  # # # przydatnosc lesna rolnej
                    podatnosc = licz_podatnosc(P1, prog_sasiedztwa)
                    # # # jezeli synteza oraz jezeli ps >5, zeby latac ewidentne dziury
                    if podatnosc > 0.3:
                        las_rol1[x1, y1] = 1
                        liczba_zal = liczba_zal +1
                        # # # latamy teraz ewentualnie powstale dziury
                        licz_sasiedztwo(x1, y1, True)
                        if zalesienie_dod == 1:
                            zalesianie_dodatkowej(x1, y1)
                        losowanie = 0
                 except:
                        return
            else:
                return
        iterator +=1
        if iterator >1000:
              return
        
#kod wyglada na popieprzony - chyba na razie wywalamy
def zalesianie_dodatkowej(x2, y2):
    global liczba_zal
    kontrolka3 = 0
    break_dodatkowy = 0
    while kontrolka3 != 1:
        r_bezp1 = random.randint(-1, 1)
        r_bezp2 = random.randint(-1, 1)
        if r_bezp1 == 0:
            r_bezp1 = 1
        if r_bezp2 == 0:
            r_bezp2 = 1
        x3 = x2 + r_bezp1
        if x3 > dlugosc:
            x3 = dlugosc
        y3 = y2 + r_bezp2
        if y3 > szerokosc:
            y3 = szerokosc
        if las_rol1[x3, y3] == 0:
            las_rol1[x3, y3] = 1
            liczba_zal = liczba_zal + 1
            kontrolka3 = 1
        break_dodatkowy += 1
        if break_dodatkowy > 20:
            break

def liczenie_popytu(liczba_lasu_wejsciowa, procentowe_tempo, lata, liczba_pikseli):
    procentowe_tempo = procentowe_tempo/100
    wzrost = liczba_lasu_wejsciowa*pow(1.000+procentowe_tempo, lata)
    procentowa = wzrost/liczba_pikseli
    if procentowa > 1:
        procentowa =0.95
    print "docelowo ma byc %s procent lasu" %str(procentowa)
    return wzrost

#moze trzeba przesunac wszelkie liczenie parametrow, a takze liczenie popytu do osobnego skryptu. zapisac te wartosci np w kolumnie atrybutowej
def liczenie_popytu_proporcjonalnego(liczba_lasu_wejsciowa, ha_lasu, liczba_lat, liczba_pikseli):
    wzrost = liczba_lasu_wejsciowa + liczba_pikseli/100*ha_lasu*liczba_lat
    procentowa = wzrost/liczba_pikseli
    if procentowa > 1:
            procentowa =0.95
    print "docelowo ma byc %s procent lasu" %str(procentowa)
    return wzrost

arcpy.CheckOutExtension("3D")
arcpy.CheckOutExtension("spatial")

# folder glowny - 2 parametr ora dodatkowy folder na obszary
folder_shp = r"c:\doktorat\czemp5\konglomeraty_250\kondracki\kondracki_shp"
folder_gdrive = r"c:\doktorat\czemp5\konglomeraty_250\kondracki"
folder = folder_gdrive

arcpy.env.workspace = folder_gdrive
arcpy.env.overwriteOutput = True
lista_workspace = arcpy.ListWorkspaces()

for i in lista_workspace[70:]:
    try:
        nazwa_modelu = os.path.basename(i)
        print(nazwa_modelu)
        ## rastry wejsciowe - przydatnosc
        # podstawic raster probablility z DClue
        przydatnosc_lesna = str(i) + "\\prob_les_stand.tif"
        rast_przyd = arcpy.Raster(przydatnosc_lesna)

        ## parametry rastra przydatnosci
        maximum_przydatnosci = rast_przyd.maximum
        przyd_mean = rast_przyd.mean
        szerokosc = int(arcpy.GetRasterProperties_management(rast_przyd, "COLUMNCOUNT").getOutput(0))
        dlugosc = int(arcpy.GetRasterProperties_management(rast_przyd, "ROWCOUNT").getOutput(0))
        max_do_sredniej = maximum_przydatnosci / przyd_mean

        ## raster do tabeli numerycznej
        przydatnosc1 = arcpy.RasterToNumPyArray(przydatnosc_lesna)
        ## rastry wejsciowe - las-rol
        las_rol = str(i) + "\\las01.tif"
        las_rol_nodata = str(i) + "\\las01_nodata.tif"

        outsetnull = SetNull(las_rol, las_rol, "VALUE < -10")
        outsetnull.save(las_rol_nodata)

        las_rol1 = arcpy.RasterToNumPyArray(las_rol_nodata)
        ## parametry rastrow wejsciowych
        desc = arcpy.Describe(las_rol)
        cellSize = desc.meanCellHeight
        extent = desc.Extent
        pnt = arcpy.Point(extent.XMin, extent.YMin)

        ##folder na rastry - tworzymy w folderze glownym
        mapa_les_path = folder + "\\" + nazwa_modelu + "\\rastry_trend"

        try:
            os.stat(mapa_les_path)
        except:
            os.mkdir(mapa_les_path)

        ##folder na tabele - tworzymy w folderze glownym
        folder_tabele = folder + "\\" + nazwa_modelu + "\\tabele_trend"
        try:
            os.stat(folder_tabele)
        except:
            os.mkdir(folder_tabele)

        # NAZWA POL, RASTROW
        maup2 = folder_shp + "\\" + str(nazwa_modelu) + ".shp"
        #print(maup2)
        maup_kopia = folder + "\\wyniki_trend\\kon_trend_" + str(nazwa_modelu) + ".shp"
        arcpy.CopyFeatures_management(maup2, maup_kopia)

        # czy zalesiac dodatkowa, 1 =tak
        zalesienie_dod = 1
        # iterator glowny
        iterator2 = 0
        # LICZBA ITERACJI
        liczba_it = 500000
        # CO ILE ZAPIS
        zapis = 100000
        liczba_zal = 0
        liczba_lasu_wejsciowa = liczenie_mapy(las_rol1, iterator2, 1, 0, 0)
        procent_lasu_wejsciowy = licz_procent(las_rol1)
        popyt = "procentowy"
        liczba_lat = 47
        tempo_w_proc = 0.4
        # ha lasu na 100 ha modelu rocznie
        ha_lasu = 0.35
        licznik_zmian = 0
        liczba_zal = 0
        koniec = 0

        if popyt == "procentowy":
            liczba_lasu_docelowa = liczenie_popytu(liczba_lasu_wejsciowa, tempo_w_proc, liczba_lat, liczba_pikseli)
        else:
            #print "popyt proporcjonalny"
            liczba_lasu_docelowa = liczenie_popytu_proporcjonalnego(liczba_lasu_wejsciowa, ha_lasu, liczba_lat,
                                                                    liczba_pikseli)

        liczenie_atrybutow(maup_kopia)
        # przerobic na petle while w oparcoi o lesistosc
        for iteracja in range(liczba_it):
                if iteracja == 1:
                    liczenie_mapy(las_rol1, iterator2, 0, liczba_lasu_docelowa, -1)
                if liczba_lasu_docelowa > liczba_pikseli:
                    liczba_lasu_docelowa = liczba_pikseli * 0.95
                liczba_zalesiona = liczba_lasu_wejsciowa + liczba_zal
                if liczba_zalesiona >= liczba_lasu_docelowa:
                    print("gratuluje, mamy juz %s pikseli lesnych, konczymy" % liczba_zalesiona, iteracja)
                    liczenie_mapy(las_rol1, iterator2, 0, liczba_lasu_docelowa, 1)
                    break

                iterator2 = iterator2 + 1
                losowanie(iterator2)
                if iterator2 % zapis == 0:
                    liczenie_mapy(las_rol1, iterator2, 0, liczba_lasu_docelowa, 0)
                    #print liczba_lasu_docelowa
                    #print liczba_zalesiona
    except:
        print("dsa")