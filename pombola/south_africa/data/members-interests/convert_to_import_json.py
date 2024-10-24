#!/usr/bin/env python

# Take the json in the file given as first argument and convert it to the JSON
# format needed for import. Should do all cleanup of data and removal of
# unneeded entries too.

import json
import os
import re
import sys

import django
import urllib

from django.db.models import Q
from django.utils.text import slugify

script_dir = os.path.basename(__file__)
base_dir = os.path.join(script_dir, "../../../../..")
app_path = os.path.abspath(base_dir)
sys.path.append(app_path)


settings_module = "pombola.settings.south_africa"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_module)
django.setup()
from pombola.core.models import Person

class Converter(object):

    groupings = []

    ditto_marks = [
        "\"",
        "\" \"",
    ]

    # Change this to True to enable little bits of helper code for finding new
    # slug corrections:
    finding_slug_corrections = False

    parties = ["ACDP", "AIC", "AL JAMA-AH", "ANC", "ATM", "COPE", "DA", "EFF", "FF PLUS", "GOOD", "IFP", "NFP", "PAC", "UDM"]
    unique_case_surname = ["ABRAHAM NTANTISO", "BODLANI MOTSHIDI", "LE GOFF", "MAZZONE MICHAEL", "MC GLUWA", "VAN ZYL", "NTLANGWINI LOUW", "DE BRUYN", "DENNER JORDAAN", "DU TOIT", "VAN STADEN"]

    slug_corrections = {
        "albert-theo-fritz": "albert-fritz",
        "albertinah-nomathuli-luthuli": "a-n-luthuli",
        "amos-matila": "amos-gerald-matila",
        "andre-gaum": "andre-hurtley-gaum",
        "andrew-louw": "a-louw",
        "anele-mda": "a-mda",
        "anton-alberts": "anton-de-waal-alberts",
        "archibold-mzuvukile-figlan": "a-m-figlan",
        "archibold-nyambi": "archibold-jomo-nyambi",
        "arthur-ainslie": "arthur-roy-ainslie",
        "bafunani-aaron-mnguni": "bafumani-aaron-mnguni",
        "barbara-anne-hogan": "b-a-hogan",
        "barbara-thompson": "barbara-thomson",
        "bertha-mabe": "bertha-peace-mabe",
        "beryl-ferguson": "beryl-delores-ferguson",
        "beverley-lynnette-abrahams": "beverley-lynette-abrahams",
        "bhekizizwe-abram-radebe": "bhekiziswe-abram-radebe",
        "bonginkosi-dhlamini": "bonginkosi-dlamini",
        "bonisile-alfred-nesi": "bonisile-nesi",
        "busisiwe-mncube": "busisiwe-veronica-mncube",
        "butana-moses-komphela": "b-m-komphela",
        "buyelwa-patience-sonjica": "b-p-sonjica",
        "buyiswa-diemu": "buyiswa-cornelia-diemu",
        "buyiswa-diemublaai": "buyiswa-cornelia-diemu",
        "cassel-mathale": "cassel-charlie-mathale",
        "charel-de-beer": "charel-jacobus-de-beer",
        "constance-mosimane": "constance-kedibone-kelekegile-mosimane",
        "cq-madlopha": "celiwe-qhamkile-madlopha",
        "crosby-mpozo-moni": "crosby-mpoxo-moni",
        "dalitha-boshigo": "dalitha-fiki-boshigo",
        "danny-montsitsi": "sediane-danny-montsitsi",
        "dennis-bloem": "dennis-victor-bloem",
        "dennis-gamede": "dumisani-dennis-gamede",
        "desiree-van-der-walt": "d-van-der-walt",
        "dina-deliwa-pule": "dina-deliwe-pule",
        "dirk-feldman": "dirk-benjamin-feldman",
        "dj-stubbe": "dirk-jan-stubbe",
        "doris-nompendlko-ngcengwane": "nompendlko-doris-ngcengwane",
        "dudu-chili": "dudu-olive-chili",
        "duduzile-sibiya": "dudu-sibiya",
        "dumisani-ximbi": "dumsani-livingstone-ximbi",
        "ebrahim-ebrahim": "ebrahim-ismail-ebrahim",
        "elza-van-lingen": "elizabeth-christina-van-lingen",
        "emmanuel-nkosinathi-mandlenkosi-mthethwa": "emmanuel-nkosinathi-mthethwa",
        "enoch-godongwana": "e-godongwana",
        "ernst-eloff": "ernst-hendrik-eloff",
        "faith-bikani": "faith-claudine-bikani",
        "gbd-mcintosh": "graham-brian-douglas-mc-intosh",
        "gelana-sindane": "gelana-sarian-sindane",
        "geoffery-quinton-mitchell-doidge": "g-q-m-doidge",
        "geolatlhe-godfrey-oliphant": "gaolatlhe-godfrey-oliphant",
        "geordin-hill-lewis": "geordin-gwyn-hill-lewis",
        "george-boinamo": "george-gaolatlhe-boinamo",
        "gloria-borman": "gloria-mary-borman",
        "graham-peter-dalziel-mackenzie": "graham-peter-dalziel-mac-kenzie",
        "gratitude-bulelani-magwanishe": "gratitude-magwanishe",
        "gregory-krumbock": "gregory-rudy-krumbock",
        "gwedoline-lindiwe-mahlangu-nkabinde": "g-l-mahlangu-nkabinde",
        "helen-line": "helen-line-hendriks",
        "hendrietta-bogopane-zulu": "hendrietta-ipeleng-bogopane-zulu",
        "herman-groenewald": "hermanus-bernadus-groenewald",
        "hildah-sizakele-msweli": "hilda-sizakele-msweli",
        "isaac-mfundisi": "isaac-sipho-mfundisi",
        "ismail-vadi": "i-vadi",
        "jac-bekker": "jacobus-marthinus-g-bekker",
        "james-lorimer": "james-robert-bourne-lorimer",
        "jan-gunda": "jan-johannes-gunda",
        "jf-smalle": "jacobus-frederik-smalle",
        "johanna-fredrika-terblanche": "johanna-fredrika-juanita-terblanche",
        "john-moepeng": "john-kabelo-moepeng",
        "joseph-job-mc-gluwa": "joseph-job-mcgluwa",
        "keith-muntuwenkosi-zondi": "k-m-zondi",
        "kenneth-raselabe-meshoe": "kenneth-raselabe-joseph-meshoe",
        "kennett-andrew-sinclair": "kenneth-andrew-sinclair",
        "lekaba-jack-tolo": "l-j-tolo",
        "lemias-buoang-mashile": "buoang-lemias-mashile",
        "leonard-ramatlakana": "leonard-ramatlakane",
        "liezl-van-der-merwe": "liezl-linda-van-der-merwe",
        "lulama-mary-theresa-xingwana": "lulama-marytheresa-xingwana",
        "lusizo-makhubela-mashele": "lusizo-sharon-makhubela-mashele",
        "lydia-sindiswe-chikunga": "lydia-sindisiwe-chikunga",
        "machejane-alina-rantsolase": "m-a-rantsolase",
        "mafemane-makhubela": "mafemane-wilson-makhubela",
        "maite-emely-nkoana-mashabane": "maite-emily-nkoana-mashabane",
        "makgathatso-pilane-majake": "makgathatso-charlotte-chana-pilane-majake",
        "makhenkezi-arnold-stofile": "m-a-stofile",
        "makone-collen-maine": "mokoane-collen-maine",
        "mandlenkosi-enock-mbili": "m-e-mbili",
        "mark-harvey-steele": "m-h-steele",
        "mary-anne-lindelwa-dunjwa": "mary-ann-lindelwa-dunjwa",
        "masefako-dikgale": "masefako-clarah-digkale",
        "matome-mokgobi": "matome-humphrey-mokgobi",
        "mavis-nontsikelelo-magazi": "n-m-magazi",
        "mavis-ntebaleng-matladi": "m-n-matladi",
        "max-vuyisile-sisuslu": "max-vuyisile-sisulu",
        "mbhazima-samuel-shilowa": "m-s-shilowa",
        "mbuyiselo-jacobs": "mbuyiselo-patrick-jacobs",
        "membathisi-mphumzi-shepherd-mdladlana": "m-m-s-mdladlana",
        "meriam-phaliso": "meriam-nozibonelo-phaliso",
        "michael-de-villiers": "michael-jacobs-roland-de-villiers",
        "michael-james-ellis": "m-j-ellis",
        "mmatlala-boroto": "mmatlala-grace-boroto",
        "mninwa-mahlangu": "mninwa-johannes-mahlangu",
        "mntombizodwa-florence-nyanda": "n-f-nyanda",
        "mogi-lydia-moshodi": "moji-lydia-moshodi",
        "mohammed-sayedali-shah": "mohammed-rafeek-sayedali-shah",
        "mondli-gungubele": "m-gungubele",
        "mosie-anthony-cele": "mosie-antony-cele",
        "mpane-mohorosi": "mpane-martha-mohorosi",
        "n-d-ntwanambi": "nosipho-dorothy-ntwanambi",
        "nolitha-yvonne-vukuza-linda": "n-y-vukuza-linda",
        "noluthando-agatha-mayende-sibiya": "n-a-mayende-sibiya",
        "nomzamo-winnie-madikizela-mandela": "nomzamo-winfred-madikizela-mandela",
        "nonkumbi-bertha-gxowa": "n-b-gxowa",
        "ntombikhayise-nomawisile-sibhida": "ntombikayise-nomawisile-sibhida",
        "ntombikhayise-nomawisile-sibhidla": "ntombikayise-nomawisile-sibhida",
        "obed-bapela": "kopeng-obed-bapela",
        "onel-de-beer": "onell-de-beer",
        "pakishe-motsoaledi": "pakishe-aaron-motsoaledi",
        "patrick-chauke": "h-p-chauke",
        "paul-mashatile": "shipokasa-paulus-mashatile",
        "pearl-petersen-maduna": "pearl-maduna",
        "petronella-catharine-duncan": "petronella-catherine-duncan",
        "petrus-johannes-christiaan-pretorius": "p-j-c-pretorius",
        "phillip-david-dexter": "p-d-dexter",
        "rachel-rasmeni": "rachel-nomonde-rasmeni",
        "radhakrishna-lutchmana-padayachie": "r-l-padayachie",
        "raseriti-tau": "raseriti-johannes-tau",
        "rebecca-m-motsepe": "rebecca-mmakosha-motsepe",
        "refilwe-junior-mashigo": "refilwe-modikanalo-mashigo",
        "regina-lesoma": "regina-mina-mpontseng-lesoma",
        "rejoice-thizwilondi-mabudafhasi": "thizwilondi-rejoyce-mabudafhasi",
        "richard-baloyi": "masenyani-richard-baloyi",
        "robert-lees": "robert-alfred-lees",
        "roland-athol-trollip": "roland-athol-price-trollip",
        "royith-bhoola": "royith-baloo-bhoola",
        "salamuddi-abram": "salamuddi-salam-abram",
        "sam-mazosiwe": "siphiwo-sam-mazosiwe",
        "sanna-keikantseeng-molao-now-plaatjie": "sanna-keikantseeng-plaatjie",
        "sanna-plaatjie": "sanna-keikantseeng-plaatjie",
        "seeng-patricia-lebenya-ntanzi": "s-p-lebenya-ntanzi",
        "sherphed-mayatula": "shepherd-malusi-mayatula",
        "sherry-chen": "sheery-su-huei-cheng",
        "sicelo-shiceka": "s-shiceka",
        "siyabonga-cwele": "siyabonga-cyprian-cwele",
        "stella-tembisa-ndabeni-abrahams": "stella-tembisa-ndabeni",
        "suhla-james-masango": "s-j-masango",
        "swaphi-h-plaatjie": "swaphi-hendrick-plaatjie",
        "swaphi-plaatjie": "swaphi-hendrick-plaatjie",
        "teboho-chaane": "teboho-edwin-chaane",
        "thabo-makunyane": "thabo-lucas-makunyane",
        "thandi-vivian-tobias-pokolo": "thandi-vivian-tobias",
        "thembalani-waltemade-nxesi": "thembelani-waltermade-nxesi",
        "tim-harris": "timothy-duncan-harris",
        "tjheta-mofokeng": "tjheta-makwa-harry-mofokeng",
        "tlp-nwamitwa-shilubana": "tinyiko-lwandlamuni-phillia-nwamitwa-shilubana",
        "tovhowani-josephine-tshivhase": "t-j-tshivhase",
        "trevor-john-bonhomme": "trevor-bonhomme",
        "tshenuwani-simon-farisani": "t-s-farisani",
        "tshiwela-elidah-lishivha": "tshiwela-elida-lishivha",
        "velly-manzini": "velly-makasana-manzini",
        "willem-faber": "willem-frederik-faber",
        "willem-phillips-doman": "w-p-doman",
        "zephroma-dubazana": "zephroma-sizani-dubazana",
        "zephroma-sizani-dlamini-dubazana": "zephroma-sizani-dubazana",
        "zisiwe-balindlela": "zisiwe-beauty-nosimo-balindlela",
        "zoliswa-kota-fredericks": "zoliswa-albertina-kota-fredericks",
        "zukiswa-rantho": "daphne-zukiswa-rantho",
        "seiso-mohai": "seiso-joel-mohai",
        "belinda-bozzoli-van-onsellen": "belinda-bozzoli",
        "micheal-cardo": "michael-john-cardo",
        "zephroma-dlamini-dubazana": "zephroma-sizani-dubazana",
        "pravin-jamnadas-gordhan": "pravin-gordhan",
        "barnard-joseph": "bernard-daniel-joseph",
        "diane-kohler": "dianne-kohler-barnard",
        "dean-macpherson": "dean-william-macpherson",
        "thembekile-majola": "richard-majola",
        "edwin-makue": "eddie-makue",
        "mmoba-malatsi-seshoka": "mmoba-solomon-seshoka",
        "suhla-masango": "bridget-staff-masango",
        "lindiwe-maseko": "maseko-lindiwe",
        "shipokosa-mashatile": "shipokasa-paulus-mashatile",
        "comely-maxegwana": "humphrey-maxegwana",
        "lungi-mnganga-gcabashe": "lungi-annette-mnganga-gcabashe",
        "pumzile-mnguni": "phumzile-justice-mnguni",
        "mohapi-mohapi": "mohapi-jihad-mohapi",
        "charles-nqakula": "c-nqakula",
        "bhekiziwe-radebe": "bhekiziswe-abram-radebe",
        "david-ross": "david-christie-ross",
        "olifile-sefako": "olefile-sefako",
        "sheila-shope-sithole": "sheila-coleen-nkhensani-sithole",
        "christiaan-smit": "christiaan-frederik-beyers-smit",
        "makhotso-magdaline-sotyu": "makhotso-magdeline-sotyu",
        "johnna-terblanche": "johanna-fredrika-juanita-terblanche",
        "thandi-tobias-pokolo": "thandi-vivian-tobias",
        "tshoganetso-tongwane-gasebonwe": "tshoganetso-mpho-adolphina-tongwane",
        "shiella-xego-sovita": "sheilla-tembalam-xego-sovita",
        "winile-zondi": "wp-zondi",
        "lindiwe-zulu": "l-d-zulu",
        "lungelwa-zwane": "ll-zwane",
        "mamonare-chueu": "chueu-patricia",
        "stanford-gana": "makashule-gana",
        "hendrik-kruger": "hendrik-christiaan-crafford-kruger",
        "dipuo-letsatsi-duba": "ms-letsatsi-duba-db",
        "nomaindiya-mfeketo": "nomaindiya-cathleen-mfeketho",
        "claudia-ndaba": "ndaba-nonhlanhla",
        "maureen-scheepers": "m-scheepers",
        "nomaindiya-cathleen-mfeketo": "nomaindiya-cathleen-mfeketho",
        "tshoganetso-mpho-adolphina-gasebonwe": "tshoganetso-mpho-adolphina-gasebonwe-tongwane",
        "mntomuhle-khawula": "m-khawula",
        "thembekile-richard-majola": "richard-majola",
        "natasha-mazzone": "natasha-wendy-anita-michael",
        "zukiswa-ncitha": "zukiswa-veronica-ncitha",
        "cathlene-labuschagne": "cathleen-labuschagne",
        "tandi-gloria-mpambo-sibhukwana": "thandi-gloria-mpambo-sibhukwana",
        "tandi-mpambo-sibhukwana": "thandi-gloria-mpambo-sibhukwana",
        "marshall-mzingisi-dlamini": "mzingisi-marshall-dlamini",
        "hlengiwe-octavia-maxon": "hlengiwe-octavia-hlophe",
        "hlengiwe-maxon": "hlengiwe-octavia-hlophe",
        "norbet-buthelezi": "sfiso-norbert-buthelezi",
        "christian-hattingh": "chris-hattingh",
        "karen-jooste-de-kock": "karen-de-kock",
        "ntombovuyo-mente-nqweniso": "ntombovuyo-veronica-nqweniso",
        "ockers-stefanus-terblanche": "ockert-stefanus-terblanche",
        "patrick-maloyi": "nono-maloyi",
        "ghaleb-cachalia": "ghaleb-cachalia",
        "archibold-figlan": "a-m-figlan",
        "hlengiwe-hlophe-maxon": "hlengiwe-octavia-hlophe",
        "nkagisang-koni-mokgosi": "nkagisang-poppy-mokgosi",
        "terrence-mpanza": "terence-skhumbuzo-mpanza",
        "phoebe-abraham-ntantiso": "noxolo-abraham-ntantiso",
        "hlengiwe-o-hlophe-mkhaliphi": "hlengiwe-octavia-hlophe",
        "mohammed-hoosen": "mohammed-haniff-hoosen",
        "rainey-hugo": "reiney-thamie-hugo",
        "gwede-samson-mantashe": "gwede-mantashe",
        "moses-masango": "moses-siphosezwe-amos-masango",
        "joseph-mc-gluwa": "joseph-job-mcgluwa",
        "lehlohonolo-mokoena": "lehlohonolo-goodwill-mokoena",
        "busisiwe-ndlovu": "busisiwe-clarah-ndlovu",
        "gwen-ngwenya": "amanda-ngwenya",
        "neliswa-nkonyeni": "np-nkonyeni",
        "hendrik-schmidt": "hendrik-cornelius-schmidt",
        "zolile-xalisa": "zolile-roger-xalisa",
        "thandiwe-alina-mfulo": "alina-mfulo",
        "micheal-shackleton": "michael-stephen-shackleton",
        "muzi-enock-mthethwa": "enock-muzi-mthethwa",
        "claudia-nonhlanhla-ndaba": "ndaba-nonhlanhla",
        "thandi-ruth-modise": "thandi-modise",
        "suzan-sophie-thembekwayo": "sophie-suzan-thembekwayo",
        "mbongiseni-david-mahlobo": "mbangiseni-david-mahlobo",
        "jaqueline-motlagomang-mofokeng": "jacqueline-motlagomang-mofokeng",
        "lindiwe-christabola-bebee": "lc-bebee",
        "nothembe-hendrietta-maseko-jele": "nomathemba-hendrietta-maseko-jele",
        "sieso-joel-mohai": "seiso-joel-mohai",
        "sibongiseni-maxwell-dhlomo": "sm-dhlomo",
        "sicelo-bafuze-yabo": "bafuze-sicelo-yabo",
        "thenjiwe-mirriam-kibi": "mirriam-thenjiwe-kibi",
        "khonziwe-ntokozo-fortunate-hlonyana": "ntokozo-khonziwe-fortunate-hlonyana",
        "nokozola-ndongeni": "nokuzola-ndongeni",
        "barbara-dallas-creecy": "creecy-barbara",
        "cedrick-thomas-frolick": "cedric-thomas-frolick",
        "thandi-mpambo-sibhukwana": "thandi-gloria-mpambo-sibhukwana",
        "thlolohelo-malatji": "thlologelo-malatji",
        "tseko-washington-isaac-mafanya": "washington-tseko-isaac-mafanya",
        "ronald-patumedi-moroatshehla": "patamedi-ronald-moroatshehla",
        "christaan-frederik-beyers-smit": "christiaan-frederik-beyers-smit",
        "mohamed-haniff-hoosen": "haniff-mohammed-hoosen",
        "phindile-martha-mmola": "martha-phindile-mmola",
        "gcinikhaya-gordon-mpumza": "gordon-gcinikhaya-mpumza",
        "dorah-dunana-dlamini": "dd-dlamini",
        "liezel-linda-van-der-merwe": "liezl-linda-van-der-merwe",
        "lilian-nombulelo-hermans": "nombulelo-lilian-hermans",
        "ezekiel-lesiba-molala": "lesiba-ezekiel-molala",
        "mandla-isaac-rayi": "mandla-rayi",
        "sifiso-nobert-buthelezi": "sfiso-norbert-buthelezi",
        "regina-mina-mponsteng-lesoma": "regina-mina-mpontseng-lesoma",
        "anthony-hope-mankwana-papo": "papo-hope",
        "zwelizwe-lawrence-mkhize": "zwelini-lawrence-mkhize",
        "hlengiwe-octavia-mkhaliphi": "hlengiwe-octavia-hlophe",
        "thamsanqa-simon-china-dodovu": "china-dodovu",
        "faith-azwihangwisi-muthambi": "azwihangwisi-faith-muthambi",
        "supra-obakeng-ramoeletsi-mahumapelo": "supra-mahumapelo",
        "aloysias-mmusi-maimane": "mmusi-aloysias-maimane",
        "godfrey-phumulo-masualle": "phumulo-masualle",
        "nonkosi-queenie-mvana": "nonkosi-mvana",
        "frederik-jacobus-mulder": "frederik-mulder",
        "constance-tebogo-modise": "tebogo-modise",
        "elsabe-natasha-ntlangwini": "elsabe-natasha-louw",
        "lizzie-fikelephi-shabalala": "lf-shabalala",
        "mmoba-solomon-malatsi": "mmoba-solomon-seshoka",
        "slindili-ann-luthuli": "a-n-luthuli",
        "altia-sthembembile-hlongo": "altia-sthembile-hlongo",
        "chantel-valencia-king": "chantel-king",
        "elleck-mamagase-nchabeleng": "mamagase-elleck-nchabeleng",
        "fikile-devilliers-xasa": "fikile-xasa",
        "bidget-staff-masango": "bridget-staff-masango",
        "samantha-jane-graham-mare": "samantha-graham-mare",
        "okert-stefanus-terblanche": "ockert-stefanus-terblanche",
        "edward-senzo-mchunu": "es-mchunu",
        "delisile-blessing-ngwenya": "delisile-ngwenya",
        "kennth-leonard-jacobs": "kenneth-leonard-jacobs",
        "makhoni-maria-ntuli": "mm-ntuli",
        "yoliswa-nomampondomisi-yako": "yoliswa-nomampondomise-yako",
        "stella-tembisa-ndabeni": "stella-tembisa-ndabeni-abrahams",
        "pemmy-castelinah-pamella-majodina": "pemmy-majodina",
        "thomas-charles-ravenscroft-walters": "thomas-walters",
        "patekile-sango-holomisa": "sango-patekile-holomisa",
        "nkosi-zwelivelile-mandela": "zwelivelile-mandlesizwe-dalibhunga-mandela",
        "nigel-sibusiso-gumede": "sibusiso-nigel-gumede",
        "bethwel-tshilidzi-munyai": "tshilidzi-bethuel-munyai",
        "nhlagongwe-patricia-mahlo": "ms-mahlo-nhlagonwe-patricia",
        "bhekizwe-simon-nkosi": "bekizwe-simon-nkosi",
        "valentia-thokozile-malinga": "thokozile-malinga",
        "mammoga-albert-seabi": "albert-mammoga-seabi",
        "jaques-warren-william-julius": "jacques-warren-william-julius",
        "madelein-bertine-hicklin": "madeleine-bertine-hicklin",
        "johannes-mathews-wolmarans": "matthews-johannes-wolmarans",
        "lydia-moji-moshodi": "moji-lydia-moshodi",
        "marubini-lourane-lubengo": "ms-lubengo-lourane-marubini",
        "rose-mary-thandiwe-zungu": "thandiwe-rose-marry-zungu",
        "mimi-martha-gondwe": "mimmy-martha-gondwe",
        "zoyisile-edward-njadu": "edward-zoyisile-njadu",
        "brenda-thirani-mathevula": "brenda-tirhani-mathevula",
        "thembi-rhulani-siweya": "rhulani-thembi-siweya",
        "noxolo-phoebe-abraham": "noxolo-abraham-ntantiso",
        "nontando-judith-nolutshungu": "nontando-nolutshungu",
        "makosini-mishack-chabangu": "mishack-makosini-chabangu",
        "kenny-thabo-motsamai": "kenny-motsamai",
        "michelle-odette-clarke": "michele-odette-clarke",
        "amos-nkosiyakhe-masondo": "nkosiyakhe-amos-masondo",
        "thandiswa-linnen-marawu": "thandiswa-marawu",
        "melina-matshidiso-gomba": "matshidiso-melina-gomba",
        "thabang-makwetla": "sampson-phathakge-makwetla",
        "thandeka-moloko-mbamba": "thandeka-moloko-mbabama",
        "bheki-hadebe": "bheki-mathews-hadebe",
        "tina-monica-joemat-petterson": "tina-monica-joemat-pettersson",
        "haseenabanu-ismael": "haseena-ismail",
        "natasha-wendy-anita-mazonne": "natasha-wendy-anita-michael",
        "christian-hans-heinrich-husinger": "christian-hans-heinrich-hunsinger",
        "thandeka-moloko-mbamba": "thandeka-moloko-mbabama",
        "lindiwe-mjobe": "lindiwe-ntombikayise-mjobo",
        "bernice-swarts-malaba": "bernice-swarts",
        "josephine-nomsa-kubeka": "nomsa-josephina-kubheka",
        "heloise-jordaan": "heloise-denner",
        "tryphosa-mmamoloko-kubayi-ngubane": "mmamoloko-tryphosa-kubayi",
        "spies-eleanor": "eleanore-rochelle-jacquelene-spies",
        "rosina-komane": "rosina-ntshetsana-komane",
        "moletsane-moletsane": "moletsane-simon-moletsane",
        "evelyn-wilson": "evelyn-rayne-wilson",
        "anele-gxoyiya": "anele-benedict-gxoyiya",
        "lindiwe-daphney-zulu": "l-d-zulu",
        "lusizo-sharon-makhubele-mashele": "lusizo-sharon-makhubela-mashele",
        "ntombovuyo-veronica-mente": "ntombovuyo-veronica-nqweniso",
        "freitas-manuel-simao-franca-de": "manuel-simao-franca-de-freitas",
        "khalipha-thanduxolo-david": "thanduxolo-david-khalipha",
        "maake-jerome-joseph": "jerome-joseph-maake",
        "malaba-bernice-swarts": "bernice-swarts",
        # name changes confirmed in National Assembly membership document
        "buyiswa-blaai": "buyiswa-cornelia-diemu",
        "sanna-keikantseeng-molao": "sanna-keikantseeng-plaatjie",
        # 2021
        "steven-m-jafta": "steven-mahlubanzima-jafta",
        "adoonsnombuyiselo": "nombuyiselo-gladys-adoons",
        "ncamashe-zolile-burns": "zolile-burns-ncamashe",
        "phoebe-noxolo-abraham": "noxolo-abraham-ntantiso",
        "price-mike-basopu": "mike-basopu",
        "mpeko-zoliswa-albertina-kota":"zoliswa-albertina-kota-fredericks",
        "nqabayomzi-kwankwa": "nqabayomzi-lawrence-kwankwa",
        "nancy-sihlwayi":"nomadewuka-nancy-sihlwayi",
        "tsholofelo-bodlani":"tsholofelo-katlego-motshidi",
        "ghaleb-kaene-yusuf-cachalia":"ghaleb-cachalia",
        "mangosuthu-buthelezi":"mangosuthu-gatsha-buthelezi",
        "lusizo-sharon-anc-makhubelamashele":"lusizo-sharon-makhubela-mashele",
        "tyotyo-james":"tyotyo-hubert-james",
        "thlologelo-malatji":"thlologelo-collen-malatji",
        "druchen-wilma-susan-anc-newhoudt":"wilma-susan-newhoudt-druchen",
        "zwelivelile-md-mandela":"zwelivelile-mandlesizwe-dalibhunga-mandela",
        "nompendulo-mkhatshwa":"nompendulo-thobile-mkhatshwa",
        "simanga-mbuyane":"simanga-happy-mbuyane",
        "cornelius-petrus-vf-mulder":"cornelius-petrus-mulder",
        "annacleta-siwisa":"annacleta-mathapelo-siwisa",
        "julius-malema":"julius-sello-malema",
        "mpya-molebeng-modise":"moleboheng-modise",
        "eleanore-rochelle-jacquelene-da-spies":"eleanore-rochelle-jacquelene-spies",
        "emam-ahmed-munzoor-shaik":"ahmed-munzoor-shaik-emam",
        "kopeng-obed-african-national-congress-bapela":"kopeng-obed-bapela",
        "majake-makgathatso-chana-anc-pilane":"makgathatso-charlotte-chana-pilane-majake",
        "ntombi-khumalo":"ntombi-valencia-khumalo",
        "sheilla-tembalam-xego":"sheilla-tembalam-xego-sovita",
        "pemmy-cp-majodina":"pemmy-majodina",
        "khumbudzo-phophi-ntshavheni":"khumbudzo-phophi-silence-ntshavheni",
        "freitasmanuel-simao-franca-de":"manuel-simao-franca-de-freitas",
        "michele-clarke":"michele-odette-clarke",
        "nocawa-noncedo-mafu":"nocawe-noncedo-mafu",
        "mxolisa-simon-african-national-congress-sokatsha":"mxolisa-simon-sokatsha",
        "mare-samantha-jane-graham":"samantha-jane-graham",
        "machwene-rosina-semenya":"ms-semenya-machwene-rosinah",
        "lille-patricia-de":"patricia-de-lille",
        "mogamad-ganief-ebrahim-al-jama-ah-hendricks":"mogamad-ganief-ebrahim-hendricks",
        "tebogo-constance-modise":"tebogo-modise",
        "staden-philippus-adriaan-ff-van":"philippus-adriaan-van-staden",
        "gigaba-bongiwe-pricilla-mbinqo":"bongiwe-pricilla-mbinqo-gigaba",
        "pieter-ff-mey":"pieter-mey",
        "oscar-masakona-mathafa":"oscar-masarona-mathafa",
        "lindiwe-nonceba-african-national-congress-sisulu":"lindiwe-nonceba-sisulu",
        "yako-yoliswa":"yoliswa-nomampondomise-yako",
        "christopher-roosadrian":"adrian-christopher-roos",
        "thamsanqa-mabhena":"thamsanqa-bhekokwakhe-mabhena",
        "petrus-johannes-vf-groenewald":"petrus-johannes-groenewald",
        "veronica-ncita":"zukiswa-veronica-ncitha",
        "mbulelo-richmond-democratic-alliance-bara":"mbulelo-richmond-bara",
        "matodzi-merriam-ramadwa":"ms-ramadwa-matodzi-mirriam",
        "moremadi-mothapo":"madipoane-refiloe-moremadi-mothapo",
        "azwihangwisi-faith-anc-muthambi":"azwihangwisi-faith-muthambi",
        "noko-phineas-democratic-alliance-masipa":"noko-phineas-masipa",
        "ignatius-michael-ff-groenewald":"ignatius-michael-groenewald",
        "mlindi-nhanha":"mlindi-advent-nhanha",
        "natasha-wendy-anita-mazzone":"natasha-wendy-anita-michael",
        "marchesi-nomsa-innocencia-da-tarabella":"nomsa-innocencia-tarabella-marchesi",
        "skhumbuzo-terence-mpanza":"terence-skhumbuzo-mpanza",
        "villiers-jan-naude-de":"jan-naude-de-villiers",
        "phumeza-theodora-mpushe":"phumeza-mpushe",
        "motshegoane-mokgothoshirley":"shirley-motshegoane-mokgotho",
        "makhosini-mishack-chabangu":"makosini-chabangu",
        "moloko-maggie-tlou":"tlou-maggie",
        "dyk-veronica-van":"veronica-van-dyk",
        "heloise-ff-denner":"heloise-denner",
        "jomo-archibold-nyambi":"archibold-jomo-nyambi",
        "baldwin-matibe":"tshitereke-baldwin-matibe",
        "mandlenkosi-mabika":"mandlenkosi-sicelo-mabika",
        "lindiwe-mjobo":"lindiwe-ntombikayise-mjobo",
        "der-merwe-liezl-linda-van":"liezl-linda-van-der-merwe",
        "nomsa-josephine-khubheka":"nomsa-josephina-kubheka",
        "dennis-ryder":"dennis-richard-ryder",
        "nceba-hinana-hinana":"nceba-ephraim-hinana",
        "dlamini-kwati-candith-mashego":"kwati-candith-mashego-dlamini",
        "mashabane-maite-emily-nkoana":"maite-emily-nkoana-mashabane",
        "edward-njadu":"edward-zoyisile-njadu",
        "mervyn-dirks":"mervyn-alexander-dirks",
        "toit-stephanus-franszouis-ff-du":"stephanus-franszouis-du-toit",
        "zweli-mkhize":"zwelini-lawrence-mkhize",
        "ngwanamakwetle-reneiloe-eff-mashabela":"ngwanamakwetle-reneiloe-mashabela",
        "der-walt-desiree-van":"d-van-der-walt",
        "jabulile-cynthia-nightingale-anc-mkhwanazi":"jabulile-cynthia-nightingale-mkhwanazi",
        "lindiwe-daphne-zulu":"l-d-zulu",
        "zuma-nc-dlamini":"nkosazana-dlamini-zuma",
        "dorries-eunice-dlakude":"dorris-eunice-dlakude",
        "william-m-madisha":"william-mothipa-madisha",
        "anastacia-motaung":"anastasia-motaung",
        "nqakula-nosiviwe-noluthando-anc-mapisa":"nosiviwe-noluthando-mapisa-nqakula",
        "barnard-dianne-kohler":"dianne-kohler-barnard",
        "nkosiyakhe-masondo":"nkosiyakhe-amos-masondo",
        "angelina-matsie-motshekga":"matsie-angelina-motshekga",
        "magdalene-duduzile-hlengwa":"magdalena-duduzile-hlengwa",
        "sinawo-thambo":"sinawo-tambo",
        "michael-democratic-bagraim":"michael-bagraim",
        "pettersson-tina-monica-joemat":"tina-monica-joemat-pettersson",
        "david-masondo":"mr-masondo-david",
        "constance-n-mkhonto":"constance-nonhlanhla-mkhonto",
        "thembinkosi-apleni":"thembinkosi-tevin-apleni",
        "bruyn-michiel-adriaan-petrus-ff-de":"michiel-adriaan-petrus-de-bruyn",
        "violet-siwela":"violet-sizani-siwela",
        "abrahams-stella-thembisa-ndabeni":"stella-tembisa-ndabeni-abrahams",
        "james-democratic-selfe":"james-selfe",
        "mmabatho-mokause":"mmabatho-olive-mokause",
        "gobonamang-prudence-anc-marekwa":"gobonamang-prudence-marekwa",
        "kenneth-mmoiemang":"mosimanegare-kenneth-mmoiemang",
        "thandeka-mbabama":"thandeka-moloko-mbabama",
        "matthew-johannes-wolmarans":"mathews-wolmarans",
        "sbongile-audrey-zuma":"audrey-sbongile-zuma",
        "darren-democratic-bergman":"darren-bergman",
        "minnen-benedicta-maria-van":"benedicta-maria-van-minnen",
        "howard-mzwakhe-sibisichristopher":"christopher-howard-mzwakhe-sibisi",
        "reina-mina-mpontseng-lesoma":"regina-mina-mpontseng-lesoma",
        "xolisile-qayiso":"xolisile-shinars-qayiso",
        "rudy-krumbockgregory":"gregory-rudy-krumbock",
        "dumisan-fannie-mthenjane":"dumisani-fannie-mthenjane",
        "linda-moss":"linda-nellie-moss",
        "schalkwyk-sharome-renay-van":"sharome-renay-van-schalkwyk",
        "sibusiso-mdabe":"sibusiso-welcome-mdabe",
        "tseko-isaac-washington-mafanya":"washington-tseko-isaac-mafanya",
        "supra-obakeng-r-mahumapelo":"supra-mahumapelo",
        "hendrik-christiaan-crafford-democratic-alliance-kruger":"hendrik-christiaan-crafford-kruger",
        "abraham-stephanus-aucampwillem":"willem-abraham-stephanus-aucamp",
        "wynand-johannes-ff-boshoff":"wynand-johannes-boshoff",
        "mosebenzi-james-zwane":"mosebenzi-joseph-zwane",
        "ronald-oozy-lamola":"ronald-ozzy-lamola",
        "frederik-jacobus-ff-mulder":"frederik-mulder",
        "emma-powell":"emma-louise-powell",
        "sibongile-makoti-khawula":"makoti-sibongile-khawula",
        "phillip-modise":"phillip-matsapole-pogiso-modise",
        "thomas-charles-ravenscroft-da-walters":"thomas-walters",
        "thembisile-phumelele-nkadimeng":"thembisile-nkadimeng",
        "jele-nomathemba-hendrietta-anc-maseko":"nomathemba-hendrietta-maseko-jele",
        "tamarin-ff-breedt":"tamarin-breedt",
        "mimmy-martha-democratic-alliance-gondwe":"mimmy-martha-gondwe",
        "betta-seneanye-lehihi":"seneanye-betta-lehihi",
        "wouter-wynand-ff-wessels":"wouter-wynand-wessels",
        "lawrence-edward-mcdonald":"lawrence-edward-mc-donald",
        "mbuyiseni-ndlozi":"mbuyiseni-quintin-ndlozi",
        "siviwe-democratic-gwarube":"siviwe-gwarube",
        # 2022
        "phoebe-noxolo-abraham-ntantiso":"noxolo-abraham-ntantiso",
        "norbert-sfiso-buthelezi": "sfiso-norbert-buthelezi",
        "bhekokwakhe-cele": "bhekokwakhe-hamilton-cele",
        "lydia-sindisiwa-chikunga":"lydia-sindisiwe-chikunga",
        "nkosazana-clarice-dlamini-zuma":"nkosazana-dlamini-zuma",
        "thamsanqa-simon-dodovu":"china-dodovu",
        "zoliswa-albertina-kota-mpeko":"zoliswa-albertina-kota-fredericks",
        "nocawe-nocawa-mafu":"nocawe-noncedo-mafu",
        "supra-ramoeletsi-mahumapelo":"supra-mahumapelo",
        "pemmy-pamela-majodina":"pemmy-majodina",
        "ponani-petunia-makhubele-marilele":"ponani-petunia-makhubele",
        "sampson-makwetla":"sampson-phathakge-makwetla",
        "christopher-malematja":"cristopher-nakampe-malematja",
        "samson-gwede-mantashe":"gwede-mantashe",
        "kwati-mashego-dlamini":"kwati-candith-mashego-dlamini",
        "tshililo-micheal-masutha":"tshililo-michael-masutha",
        "simphiwe-nomvula-mbatha":"simphiwe-gcwele-nomvula-mbatha",
        "edward-mchunu":"es-mchunu",
        "thembeka-buyisile-mchunu":"thembeka-vuyisile-buyisile-mchunu",
        "matshidiso-morwa-mfikoe":"matshidiso-morwa-annastinah-mfikoe",
        "jabulile-nightingale-mkhwanazi":"jabulile-cynthia-nightingale-mkhwanazi",
        "kenneth-mosimanegare-mmoiemang":"mosimanegare-kenneth-mmoiemang",
        "pogiso-modise":"phillip-matsapole-pogiso-modise",
        "linda-nelie-moss":"linda-nellie-moss",
        "kgoshigadi-madipoane-refiloe-moremadi-mothapo":"madipoane-refiloe-moremadi-mothapo",
        "thembisile-phemelele-nkadimeng":"thembisile-nkadimeng",
        "khumbudzo-silence-ntshavheni":"khumbudzo-phophi-silence-ntshavheni",
        "itumeleng-vutha-ntsube":"itumeleng-ntsube",
        "grace-naledi-pandor":"grace-naledi-mandisa-pandor",
        "anthony-mankwana-papo":"mankwana-christinah-mohale",
        "ntaoleng-peacock":"ntaoleng-patricia-peacock",
        "bhekiziwe-abram-radebe":"bhekiziswe-abram-radebe",
        "matodzi-mirriam-ramadwa":"ms-ramadwa-matodzi-mirriam",
        "mthenjwa-amos-zondi":"mthenjwa-amon-zondi",
        "mosebenze-joseph-zwane":"mosebenzi-joseph-zwane",
        "alexandra-amelia-abrahams":"alexandra-lilian-amelia-abrahams",
        "wendy-alexander":"wendy-robyn-alexander",
        "willem-stephanus-aucamp":"willem-abraham-stephanus-aucamp",
        "motshidi-tsholofelo-katlego-bodlani":"tsholofelo-katlego-motshidi",
        "timothy-brauteseth":"timothy-james-brauteseth",
        "samantha-jane-graham-mare": "samantha-jane-graham",
        "christian-hans-hunsinger":"christian-hans-heinrich-hunsinger",
        "haseenabanu-ismail":"haseena-ismail",
        "dennis-joseph":"denis-joseph",
        "karabo-khakhau":"karabo-lerato-khakhau",
        "hendrik-christiaan-kruger":"hendrik-christiaan-crafford-kruger",
        "michael-natasha-wendy-anita-mazzone":"natasha-wendy-anita-michael",
        "tsepo-winson-mhlongo":"tsepo-winston-mhlongo",
        "nicholas-george-myburgh":"nicholas-georg-myburgh",
        "adrian-roos":"adrian-christopher-roos",
        "eleanore-jacquelene-spies":"eleanore-rochelle-jacquelene-spies",
        "annerie-magdalena-weber":"annerie-maria-magdalena-weber",
        "makosini-mishack-chabangu":"makosini-chabangu",
        "phiwaba-madokwe":"piaba-madokwe",
        "washington-isaac-mafanya":"washington-tseko-isaac-mafanya",
        "omphile-maotwe":"omphile-mankoba-confidence-maotwe",
        "ciliesta-shoana-motsepe":"ciliesta-catherine-shoana-motsepe",
        "louw-elsabe-natasha-ntlangwini":"elsabe-natasha-louw",
        "jordaan-heloise-denner":"heloise-denner",
        "brett-herron":"brett-norton-herron",
        "inkosi-elphas-mfakazeleni-buthelezi":"elphas-mfakazeleni-buthelezi",
        "inkosi-russel-nsikayezwe-cebekhulu":"russel-nsikayezwe-cebekhulu",
        "nhlanhla-mzungezwa-hadebe":"nhlanhla-hadebe",
        "inkosi-bhekizizwe-nivard-luthuli":"bhekizizwe-nivard-luthuli",
        "christopher-mzwakhe-sibisi":"christopher-howard-mzwakhe-sibisi",
        "nqabayomzi-lawrence-saziso-kwankwa":"nqabayomzi-lawrence-kwankwa",
        # 2023
        "portia-tebogo-mamorobela":"tebogo-portia-mamorobela",
        "shipokosa-paulus-mashatile":"shipokosa-paul-mashatile",
        "humphrey-mdumzeli-zondelele-mmemezi":"humphrey-mmemezi",
        "motalane-dewet-monakedi":"motalane-monakedi",
        "maropene-lydia-ramokgopa":"maropene-ramokgopa",
        "mpho-parks-tau":"mpho-parks-franklyn-tau",
        "mbulelo-jonathan-magwala":"mbulelelo-jonathan-magwala",
        "mzwanele-manyi":"mzwanele-jimmy-manyi",
        # Garbage entries
        "control-flag-ict": None,
    }

    category_sort_orders = {
        "SHARES AND OTHER FINANCIAL INTERESTS": 1,
        "REMUNERATED EMPLOYMENT OUTSIDE PARLIAMENT": 2,
        "DIRECTORSHIP AND PARTNERSHIPS": 3,
        "CONSULTANCIES OR RETAINERSHIPS": 4,
        "SPONSORSHIPS": 5,
        "GIFTS AND HOSPITALITY": 6,
        "BENEFITS": 7,
        "TRAVEL": 8,
        "LAND AND PROPERTY": 9,
        "PENSIONS": 10,
        "CONTRACTS": 11,
        "TRUSTS": 12,
        "ENCUMBERANCES": 13,
    }

    def __init__(self, filename):
        self.filename = filename
        self.mp_count = {}

    def convert(self):
        data = self.extract_data_from_json()

        self.extract_release(data)
        self.extract_entries(data)

        return self.produce_json()

    def extract_release(self, data):
        source_url = data['source']
        year = data['year']
        date = data['date']

        source_filename = re.sub(r'.*/(.*?)\.pdf', r'\1', source_url)
        source_name = urllib.unquote(source_filename).replace('_', ' ').strip()

        self.release = {
            "name": "Parliament Register of Members' Interests " + year,
            "date": date,
            "source_url": source_url,
        }

    def extract_entries(self, data):
        for register_entry in data['register']:
            for raw_category_name, entries in register_entry.items():
                # we only care about entries that are arrays
                if type(entries) != list:
                    continue

                # go through all entries stripping off extra whitespace from
                # keys and values
                for entry in entries:
                    for key in entry.keys():

                        # correct common scraper heading error
                        key_to_use = key.strip()
                        if key_to_use == 'Benefits' and raw_category_name.strip() == "TRUSTS":
                            key_to_use = "Details Of Benefits"

                        entry[key_to_use] = entry.pop(key).strip()

                    if entry.get('No') == 'Nothing to disclose':
                        del entry['No']

                # Need to be smart about values that are just '"' as these are dittos of the previous entries.
                previous_entries = []
                for entry in entries:
                    if len(previous_entries):
                        for key in entry.keys():
                            if entry[key] in self.ditto_marks:
                                for previous in reversed(previous_entries):
                                    if key in previous:
                                        entry[key] = previous[key]
                                        break
                                # Replacement may not have been found, warn
                                # if entry[key] in self.ditto_marks:
                                #     sys.stderr.write("----------- Could not find previous entry for ditto mark of '{0}'\n".format(key))
                                #     sys.stderr.write(str(previous_entries) + "\n")
                                #     sys.stderr.write(str(entry) + "\n")
                    previous_entries.append(entry)

                # Filter out entries that are empty
                entries = [e for e in entries if len(e)]

                if len(entries) == 0:
                    continue

                grouping = {
                    "release": self.release,
                    "entries": entries,
                }

                # Extract the category name we are interested in
                category_name = raw_category_name.strip()
                category_name = re.sub(r'^\d+\.\s*', '', category_name)

                grouping['category'] = {
                    "sort_order": self.category_sort_orders[category_name],
                    "name": category_name,
                }

                # Work out who the person is
                person_slug = self.mp_to_person_slug(register_entry['mp'])
                if not person_slug:
                    continue  # skip if no slug
                self.mp_count[person_slug] = register_entry['mp']
                grouping['person'] = {
                    "slug": person_slug
                }

                self.groupings.append(grouping)
            # break # just for during dev

    def mp_to_person_slug(self, mp):
        # NOTE: 2020 no longer has the party in the name and the names are rearranged
        pattern = r'\b(?:{})\b'.format('|'.join(map(re.escape, self.parties)))

        if (mp == "ABRAHAM NTANTISOPHOEBE NOXOLO ANC"):
            mp = "ABRAHAM NTANTISO PHOEBE NOXOLO ANC"

        name_only = re.sub(pattern, '', mp)
        # special case surnames
        for surname in self.unique_case_surname:
            if name_only.startswith(surname):
                name_ordered = re.sub(r'^(\w+\b\s+\w+\b)\s+(.*)$', r'\2 \1', name_only)
                break
            else:
                name_ordered = re.sub(r'(.*?) (.*)', r'\2 \1', name_only)
        slug = slugify(name_ordered)

        # Check if there is a known correction for this slug
        slug = self.slug_corrections.get(slug, slug)

        # Sometimes we know we can't resolve the person
        if slug is None:
            return None

        try:
            person = Person.objects.get(slug=slug)
            return person.slug
        except Person.DoesNotExist:
            try:
                name_base = re.findall(r'(.*?) (.*)', mp.replace('-', ','))
                if name_base:
                    name_parts = name_base[0]
                    person = Person.objects.get(Q(slug__contains=slugify(name_parts[0])) & Q(slug__contains=slugify(name_parts[1])))
                    return person.slug
                else:
                    return None
            except Person.DoesNotExist:
                last_name = mp.split(' ')[-1]

                possible_persons = Person.objects.filter(
                    legal_name__icontains=last_name)

                if self.finding_slug_corrections and possible_persons.count() == 1:
                    possible_slug = possible_persons.all()[0].slug
                    self.slug_corrections[slug] = possible_slug
                    return possible_slug

                for person in possible_persons:
                    print('perhaps: "{0}": "{1}",'.format(slug, person.slug))
                else:
                    print("no possible matches for {0}".format(slug))

                raise Exception(
                    "Slug {0} not found, please find matching slug and add it to the slug_corrections".format(slug))

    def produce_json(self):
        data = self.groupings

        combined_data = self.combine_data(data)

        out = json.dumps(combined_data, indent=4, sort_keys=True)
        return re.sub(r' *$', '', out, flags=re.M)

    def combine_data(self, data):
        """
        Manipulate the data so that there are no duplicates of person and
        category, and sort data so that it is diff-able.
        """
        sorted_data = sorted(
            data,
            key=lambda x: x['person']['slug'] + ':' + x['category']['name']
        )

        combined_data = []

        for entry in sorted_data:
            # check if the last entry of combined_data has same person and
            # category. If so add entries to that, otherwise append whole thing.

            if len(combined_data):
                last_entry = combined_data[-1]
            else:
                last_entry = None

            if last_entry and last_entry['person']['slug'] == entry['person']['slug'] and last_entry['category']['name'] == entry['category']['name']:
                last_entry['entries'].extend(entry['entries'])
            else:
                combined_data.append(entry)

        return combined_data

    def extract_data_from_json(self):
        with open(self.filename) as fh:
            return json.load(fh)


if __name__ == "__main__":
    converter = Converter(sys.argv[1])
    output = converter.convert()
    print(output)

    if converter.finding_slug_corrections:
        print("\n\n")
        print("#### COPY THIS TO slug_corrections and s/null/None/ :) ####")
        print("\n\n")
        print(json.dumps(converter.slug_corrections, indent=4, sort_keys=True))
        print("\n\n")
