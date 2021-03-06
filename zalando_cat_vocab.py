from zalando_downloader import *
from zalando_dataset import *
import operator
import pickle

CAT_VOCAB = {}
NAME_FILTER = set([])
MAIN_CAT_NAMES = set([])

CAT_ZALDOWN = ZalandoDownloader()
CAT_ZALDOWN.section = "categories"

def add_cat(catkey, language="it-IT"):
    if catkey not in CAT_VOCAB:
        global CAT_ZALDOWN
        CAT_ZALDOWN = ZalandoDownloader(language=language)
        CAT_ZALDOWN.section = "categories"
        CAT_ZALDOWN.parameters = []
        CAT_ZALDOWN.parameters.append(("key", catkey))
        res = CAT_ZALDOWN.get_json()
        if "content" in res and len(res['content']) == 1:
            cat = res['content'][0]
            assert cat['key'] == catkey
            CAT_VOCAB[catkey] = {}
            CAT_VOCAB[catkey]['name'] = cat['name']
            CAT_VOCAB[catkey]['key'] = cat['key']
            CAT_VOCAB[catkey]['parentKey'] = cat['parentKey'] if 'parentKey' in cat else ""
            CAT_VOCAB[catkey]['childKeys'] = cat['childKeys'] if 'childKeys' in cat else []

def save_cache(cachefilename="defaultcache"):
    with open(cachefilename+'.pkl', 'wb') as cachefile:
        pickle.dump(CAT_VOCAB, cachefile, pickle.HIGHEST_PROTOCOL)

def load_cache(cachefilename="defaultcache"):
    try:
        with open(cachefilename + '.pkl', 'rb') as cachefile:
            CAT_VOCAB.update(pickle.load(cachefile))
    except FileNotFoundError:
        pass

def load_main_cat_names(maincatname="defaultmaincatnames.txt"):
    lista_main_cat_names = []
    try:
        with open(maincatname, 'r') as maincatfile:
            for line in maincatfile:
                lista_main_cat_names.append(line.rstrip())
    except FileNotFoundError:
        pass
    MAIN_CAT_NAMES.update(lista_main_cat_names)

def load_filter(filtername="defaultfilter.txt"):
    lista_filtri = []
    try:
        with open(filtername, 'r') as filterfile:
            for line in filterfile:
                lista_filtri.append(line.rstrip())
    except FileNotFoundError:
        pass
    NAME_FILTER.update(lista_filtri)

def get_nomi(catkeys, language="it-IT"):
    catnames = []
    for catkey in catkeys:
        add_cat(catkey, language="it-IT")
        if catkey in CAT_VOCAB:
            catnames.append(CAT_VOCAB[catkey]['name'])
    return catnames

def get_nome(catkey):
    toret = get_nomi([catkey])
    return toret[0] if len(toret) > 0 else ""

def has_parent_key(childkey, parentkey):
    if childkey == "":
        return False
    add_cat(childkey)
    return CAT_VOCAB[childkey]['parentKey'] == parentkey

def has_parent_name(childkey, parentname):
    if CAT_VOCAB[childkey]['parentKey'] == "":
        return False
    add_cat(CAT_VOCAB[childkey]['parentKey'])
    return CAT_VOCAB[CAT_VOCAB[childkey]['parentKey']]['name'] == parentname

def has_ancestor_name(childkey, ancestorname):
    if childkey == "":
        return False
    add_cat(childkey)
    parentkey = CAT_VOCAB[childkey]['parentKey']
    return has_parent_name(childkey, ancestorname) or has_ancestor_name(parentkey, ancestorname)

def has_ancestor_key(childkey, ancestorkey):
    if childkey == "":
        return False
    add_cat(childkey)
    parentkey = CAT_VOCAB[childkey]['parentKey']
    return has_parent_key(childkey,ancestorkey) or has_ancestor_key(parentkey,ancestorkey)

def get_catkey_from_name(catname, additionalparams=[], language="it-IT", nopromo=True, nopremium=True, nosport=True):
    global CAT_ZALDOWN
    CAT_ZALDOWN = ZalandoDownloader(language=language)
    CAT_ZALDOWN.section = "categories"
    CAT_ZALDOWN.parameters = []
    CAT_ZALDOWN.parameters.append(("name", catname))
    CAT_ZALDOWN.parameters.append(("pageSize", "50"))
    CAT_ZALDOWN.parameters.extend(additionalparams)
    res = CAT_ZALDOWN.get_json()
    current_key = ""
    if "content" in res:
        cats = res['content']
        for catres in cats:
            if nopromo and "promo" in catres["key"]:
                continue
            if nopremium and "premium" in catres["key"]:
                continue
            if nosport and "sport" in catres["key"] or "sport" in catres["parentKey"] \
                or "sports" in catres["type"]:
                continue
            add_cat(catres["key"], language=language)
            #se non ho ancora scelto chiavi o la chiave che ho ora è "sopra" quella corrente
            if catres["name"] == catname \
                and (current_key == "" or has_ancestor_key(current_key, catres["key"])):
                #diventa la nuova corrente
                current_key = catres["key"]
    return current_key

def load_catkeys_from_namefile(namefile="defaultmaincatnames.txt", additionalparams=[]):
    lista_catkeys = []
    try:
        with open(namefile, 'r') as maincatfile:
            for line in maincatfile:
                catkey = get_catkey_from_name(line.rstrip(), additionalparams=additionalparams)
                if catkey != "":
                    lista_catkeys.append(catkey)
    except FileNotFoundError:
        pass
    return lista_catkeys

if __name__ == "__main__":
    print(load_catkeys_from_namefile("maincatnames_morespecific.txt" \
        , additionalparams=[("targetGroup", "WOMEN")]))
    # ZALDATA = ZalandoDataset(datasetpath="datasets/felpe_tshirt", mode="r")
    # maglieria_felpe_pairings = []
    # #maglieria_felpe_count = 0
    # tshirt_top_pairings = []
    # #tshirt_top_count = 0
    # load_cache()
    # load_filter()
    # for art_key, attributes in ZALDATA.dataset.items():
    #     if "Maglieria & Felpe" in get_nomi(attributes['categoryKeys']):
    #         maglieria_felpe_pairings.extend(attributes['pairings'])
    #         #maglieria_felpe_count += len(attributes['pairings'])
    #     elif "T-shirt & Top" in get_nomi(attributes['categoryKeys']):
    #         tshirt_top_pairings.extend(attributes['pairings'])
    #         #tshirt_top_count += len(attributes['pairings'])
    # save_cache()
    # maglieria_felpe_pairing_stats = {}
    # for maglieria_felpe_pairing in maglieria_felpe_pairings:
    #     #potrei ancora fare un controllo dell'ancestorname e assicurarmi di non contare tshirt e Top
    #     # negli abbinamenti con le felpe, e viceversa nel prossimo ciclo, ha senso?
    #     #if has_ancestormaglieria_felpe_pairing
    #     for cat_key in ZALDATA.dataset[maglieria_felpe_pairing]['categoryKeys']:
    #         if get_nome(cat_key) not in NAME_FILTER:
    #             if get_nome(cat_key) not in maglieria_felpe_pairing_stats:
    #                 maglieria_felpe_pairing_stats[get_nome(cat_key)] = 0
    #             maglieria_felpe_pairing_stats[get_nome(cat_key)] += 1
    # mfps_sorted = sorted(maglieria_felpe_pairing_stats.items(), key=operator.itemgetter(1), reverse=True)
    # tshirt_top_pairing_stats = {}
    # for tshirt_top_pairing in tshirt_top_pairings:
    #     for cat_key in ZALDATA.dataset[tshirt_top_pairing]['categoryKeys']:
    #         if get_nome(cat_key) not in NAME_FILTER:
    #             if get_nome(cat_key) not in tshirt_top_pairing_stats:
    #                 tshirt_top_pairing_stats[get_nome(cat_key)] = 0
    #             tshirt_top_pairing_stats[get_nome(cat_key)] += 1
    # ttps_sorted = sorted(tshirt_top_pairing_stats.items(), key=operator.itemgetter(1), reverse=True)

    # fout = open("report.txt", "w")
    # fout.write("Maglieria & Felpe ("+str(len(maglieria_felpe_pairings))+"): \n")
    # for cat_name, cat_count in mfps_sorted:
    #     fout.write(cat_name+":"+str(cat_count)+"\n")
    # fout.write("\n**********************************\n")
    # fout.write("T-shirt & Top ("+str(len(tshirt_top_pairings))+"): \n")
    # for cat_name, cat_count in ttps_sorted:
    #     fout.write(cat_name+":"+str(cat_count)+"\n")
    # fout.write("\n**********************************\n")
    # fout.write("Best common: \n")
    # all_cat_names = maglieria_felpe_pairing_stats.keys() | tshirt_top_pairing_stats.keys()
    # common = {}
    # disjoint = {}
    # for cat_name in all_cat_names:
    #     num_mf = 0 if cat_name not in maglieria_felpe_pairing_stats else maglieria_felpe_pairing_stats[cat_name]
    #     num_tt = 0 if cat_name not in tshirt_top_pairing_stats else tshirt_top_pairing_stats[cat_name]
    #     somma = (num_mf + num_tt) * (num_mf + num_tt)
    #     differenza = abs(num_mf - num_tt) + 1
    #     minimo = min(num_mf, num_tt) + 1
    #     #fout.write(cat_name+":"+str(somma/differenza)+"\n")
    #     common[cat_name] = somma/differenza
    #     disjoint[cat_name] = somma/minimo
    # common_sorted = sorted(common.items(), key=operator.itemgetter(1), reverse=True)
    # disjoint_sorted = sorted(disjoint.items(), key=operator.itemgetter(1), reverse=True)
    # for cat_name, cat_value in common_sorted:
    #     fout.write(cat_name+":"+str(cat_value)+"\n")
    # fout.write("\n**********************************\n")
    # fout.write("Best disjoint: \n")
    # for cat_name, cat_value in disjoint_sorted:
    #     fout.write(cat_name+":"+str(cat_value)+"\n")
    # fout.close()
