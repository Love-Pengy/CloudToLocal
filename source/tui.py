###
#  @file    tui.py
#  @author  Brandon Elias Frazier
#  @date    Dec 18, 2025
#
#  @brief   TUI For Ctldl
#
#  @copyright (c) 2025 Brandon Elias Frazier
#
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.
#
#
#################################################################################

import io
import json
import logging
import textwrap
import urllib.request
from datetime import datetime

from textual import work
from utils.logging import tui_log
from textual.content import Content
from playlists import PlaylistHandler
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual_image.widget import Image
from textual.css.query import NoMatches
from textual.app import App, ComposeResult
from textual.validation import Function, Number
from metadata import replace_metadata, MetadataCtx
from report import ReportStatus, get_report_status_str
from textual.containers import Horizontal, Grid, Container, VerticalScroll

from utils.common import (
    get_img_size_url,
    list_to_comma_str,
    comma_str_to_list,
)

from textual.widgets import (
    Footer, Header, Pretty,
    Rule, Static, Button,
    Label, Input, Checkbox,
    Select
)

MAX_THUMBNAIL_RETRIES = 5
DEFAULT_IMAGE_SIZE = (1200, 1200)
FAILURE_IMAGE_PATH = "assets/failure_white.png"
THUMBNAIL_SIZE_PRIO_LIST = ["1200", "500", "250"]


def initialize_image(in_id: str) -> Image:
    output_image = Image(id=in_id)
    output_image.loading = True
    output_image._image_width, output_image._image_height = DEFAULT_IMAGE_SIZE
    return (output_image)


async def obtain_image_from_url(url: str, in_image: Image):
    if (not in_image):
        tui_log("Image passed to obtain image is None")
        return

    elif (not url):
        tui_log("Setting failure image...")
        in_image.image = FAILURE_IMAGE_PATH
        in_image.loading = False
        return

    for i in range(0, MAX_THUMBNAIL_RETRIES):
        try:
            with urllib.request.urlopen(url) as response:
                request_response = response.read()
                in_image.image = io.BytesIO(request_response)
                break
        except Exception:
            tui_log(f"{i}: Image obtain failed...retrying")
            continue
    else:
        tui_log("Setting failure image...")
        in_image.image = FAILURE_IMAGE_PATH

    in_image.loading = False

# NOTE: It seems as though genres are user inputted into soundcloud and can therefore be malformed
#       or differently formatted than musicbrainz. To keep consistency mappings will be created
#       for all found genres ~ BEF
# TO-DO: can def find a better way of doing this, butttt do I care atm? Prolly not... ~ BEF
# TO-DO: I lied to do care... ~ BEF
SOUNDCLOUD_GENRES = [
    ("Drum & Bass", "drum and bass"),
    ("Jungle ", "jungle"),
    ("Jungle", "jungle")
]

# NOTE: This is silly, but I now have the entire list to play around with and see how long it takes
#       to load hehe ~ BEF
MUSICBRAINZ_GENRES = [
    "2 tone", "2-step", "3-step", "aak", "abhang", "aboio", "abstract hip hop", "acholitronix",
    "acid breaks", "acid house", "acid jazz", "acid rock", "acid techno", "acid trance",
    "acidcore", "acousmatic", "acoustic blues", "acoustic chicago blues", "acoustic rock",
    "acoustic texas blues", "adhunik geet", "afoxê", "african blues", "afro house", "afro rock",
    "afro trap", "afro-cuban jazz", "afro-funk", "afro-jazz", "afro-zouk",
    "afrobeat (funk/soul + West African sounds)", "afrobeats (West African urban/pop music)",
    "afropiano", "afroswing", "agbadza", "agbekor", "aggrotech", "ahwash", "aita", "akishibu-kei",
    "al jeel", "aleke", "algerian chaabi", "algorave", "alloukou", "alpenrock", "alté",
    "alternative country", "alternative dance", "alternative folk", "alternative hip hop",
    "alternative metal", "alternative pop", "alternative punk", "alternative r&b",
    "alternative rock", "amapiano", "ambasse bey", "ambient", "ambient americana", "ambient dub",
    "ambient house", "ambient noise wall", "ambient plugg", "ambient pop", "ambient techno",
    "ambient trance", "ambrosian chant", "american gamelan", "american primitive guitar",
    "americana", "amigacore", "anarcho-punk", "anatolian rock", "andalusian classical",
    "andean new age", "anglican chant", "animal sounds", "anti-folk", "aor", "apala",
    "appalachian folk", "aquacrunk", "arabesk", "arabesk rap", "arena rock", "arrocha",
    "arrocha funk", "arrocha sertanejo", "arrochadeira", "ars antiqua", "ars nova",
    "ars subtilior", "art pop", "art punk", "art rock", "art song", "artcore",
    "ashkenazi cantorial music",
    "asian rock (pluggnb subgenre - not rock from Asia)", "asmr", "assiko",
    "atmospheric black metal", "atmospheric drum and bass", "atmospheric sludge metal",
    "audio documentary", "audio drama", "autonomic", "avant-folk", "avant-garde",
    "avant-garde jazz", "avant-garde metal", "avant-garde pop", "avant-prog", "avanzada",
    "avtorskaya pesnya", "axé", "bacardi", "bachata", "bachatón", "bagad", "bagatelle", "baguala",
    "baião", "baila", "baisha xiyue", "baithak gana", "bakersfield sound", "balani show",
    "balearic beat", "balearic trance", "balinese gamelan", "balitaw", "ballad", "ballad opera",
    "ballet", "ballet de cour", "ballroom house", "baltimore club", "bambuco", "banda sinaloense",
    "bandari", "bandinha", "banga", "bantengan", "barber beats", "barbershop",
    "bard rock", "bardcore", "baroque", "baroque pop", "baroque suite", "bashment soca",
    "bass house", "bassline", "batida", "batidão romântico", "batonebi songs", "battle rap",
    "battle record", "batucada", "batuque", "baul gaan", "beach music", "beat bolha",
    "beat bruxaria", "beat fino", "beat music", "beat poetry", "beat rock (Japanese 1980s genre)",
    "beatboxing", "beatdown hardcore", "bebop", "bedroom pop", "beijing opera", "bélé",
    "belgian techno", "bend-skin", "beneventan chant", "benga", "beni", "benna", "beompae",
    "bérite club", "berlin school", "bhajan", "bhangra", "bhavageethe", "bhojpuri pop", "big band",
    "big beat", "big room house", "big room trance", "biguine", "bikutsi", "binaural beats",
    "biraha", "birdsong", "birmingham sound", "bit music", "bitpop", "black 'n' roll",
    "black ambient", "black metal", "black midi", "black noise", "blackened crust",
    "blackened death metal", "blackgaze", "bleep techno", "blue-eyed soul", "bluegrass",
    "bluegrass gospel", "blues", "blues rock", "bocet", "boduberu", "boedra", "bogino duu",
    "bolero (Cuban song)", "bolero español", "bolero son", "bolero-beat", "bomba",
    "bomba del chota", "bongo flava", "boogaloo", "boogie", "boogie rock", "boogie-woogie",
    "boom bap", "bossa nova", "bounce", "bounce beat", "bouncy techno", "bouyon", "brass band",
    "brazilian bass", "brazilian phonk", "break-in", "breakbeat", "breakbeat hardcore",
    "breakbeat kota", "breakcore", "breaks", "breakstep", "brega", "brega calypso", "brega funk",
    "briddim", "brill building", "brit funk", "britcore", "british blues", "british brass band",
    "british folk rock", "british rhythm & blues", "britpop", "bro-country", "broadband noise",
    "broken beat", "broken transmission", "brostep", "brutal death metal", "brutal prog",
    "bubblegum bass", "bubblegum dance", "bubblegum pop", "bubbling", "bubbling house",
    "buchiage trance", "budots", "bulería", "bullerengue", "burger-highlife", "burmese classical",
    "burmese mono", "burmese stereo", "burning spirits", "burrakatha", "bytebeat",
    "byzantine chant", "c-pop", "c86", "ca trù", "cabaret", "cabo zouk", "cadence lypso",
    "cadence rampa", "cải lương", "cajun", "cakewalk", "čalgija", "calipso venezolano",
    "calypso", "campursari", "campus folk", "canción melódica", "candombe", "candombe beat",
    "cantata", "cante alentejano", "canterbury scene", "canto a lo poeta", "canto cardenche",
    "canto degli alpini (alpini song)", "cantonese opera", "cantopop", "cantoria",
    "cantu a chiterra", "cantu a tenore", "canzona", "canzone d'autore",
    "canzone napoletana (neapolitan song)", "canzone neomelodica", "cape breton fiddling",
    "cape jazz", "caporal", "capriccio", "carimbó", "carnatic classical", "carnavalito",
    "carranga", "celtic", "celtic chant", "celtic electronica", "celtic metal", "celtic new age",
    "celtic punk", "celtic rock", "central asian throat singing", "chacarera", "chachachá",
    "chalga", "chamamé", "chamamé tropical", "chamarrita açoriana", "chamarrita rioplatense",
    "chamber folk", "chamber pop", "champeta", "changa tuki", "change ringing", "changjak gugak",
    "changüí", "chanson à texte", "chanson française", "chanson québécoise", "chanson réaliste",
    "chaozhou xianshi", "chap hop", "character piece", "charanga", "chazzanut", "chèo",
    "chicago blues", "chicago bop", "chicago drill", "chicago house", "chicago soul",
    "chicano rap", "chicha", "children's music", "chilena", "chillout", "chillstep", "chillsynth",
    "chillwave", "chimayche", "chimurenga", "chinese classical", "chinese literati music",
    "chinese opera", "chinese revolutionary opera", "chipmunk soul", "chiptune", "chöd",
    "chopped and screwed", "choral symphony", "choro", "chotis madrileño", "christian hardcore",
    "christian hip hop", "christian metal", "christian rock", "christmas music", "church music",
    "chutney", "chutney soca", "cilokaq", "cinematic classical", "ciranda", "circus march",
    "city pop", "classic blues", "classic country", "classic jazz", "classic rock", "classical",
    "classical crossover", "classical period", "close harmony", "cloud rap", "club",
    "cocktail nation", "coco", "coladeira", "coldwave", "colindă", "colour bass", "comédie-ballet",
    "comedy", "comedy hip hop", "comedy rock", "comfy synth", "compas", "complextro",
    "concert band", "concertina band", "concerto", "concerto for orchestra", "concerto grosso",
    "conducted improvisation", "conga", "congolese rumba", "conscious hip hop",
    "contemporary christian", "contemporary classical", "contemporary country",
    "contemporary folk", "contemporary gospel", "contemporary jazz", "contemporary r&b",
    "contenance angloise", "contra", "cool jazz", "coon song", "copla", "corrido",
    "corrido tumbado", "cosmic country", "country", "country and irish", "country blues",
    "country boogie", "country folk", "country gospel", "country pop", "country rap",
    "country rock", "country soul", "country yodeling", "countrypolitan", "coupé-décalé",
    "cowboy poetry", "cowpunk", "crack rock steady", "crime jazz", "crossbreed", "crossover jazz",
    "crossover prog", "crossover thrash", "cruise", "crunk", "crunkcore", "crust punk", "csárdás",
    "cuarteto", "cubatón", "cuddlecore", "cueca", "cumbia", "cumbia amazónica", "cumbia argentina",
    "cumbia chilena", "cumbia colombiana", "cumbia mexicana", "cumbia norteña mexicana",
    "cumbia peruana", "cumbia pop", "cumbia rebajada", "cumbia salvadoreña", "cumbia santafesina",
    "cumbia sonidera", "cumbia turra", "cumbia villera", "cumbiatón", "cuplé", "currulao",
    "cyber metal", "cybergrind", "cyberpunk", "d-beat", "dabke", "dance", "dance-pop",
    "dance-punk", "dance-punk revival", "dance-rock", "dancefloor drum and bass", "dancehall",
    "dangak", "dangdut", "danmono", "dansband", "dansktop", "danzón", "dariacore", "dark ambient",
    "dark cabaret", "dark disco", "dark electro", "dark folk", "dark jazz", "dark plugg",
    "dark psytrance", "dark wave", "darkcore", "darkcore edm", "darkstep", "darksynth",
    "data sonification", "death 'n' roll", "death industrial", "death metal", "death-doom metal",
    "deathchant hardcore", "deathcore", "deathgrind", "deathrock", "deathstep", "dechovka",
    "deconstructed club", "deejay", "deep drum and bass", "deep funk", "deep house", "deep soul",
    "deep tech", "deep techno", "delta blues", "dembow", "demostyle", "dennery segment", "denpa",
    "depressive black metal", "descarga", "desert blues", "desert rock", "desgarrada",
    "detroit techno", "detroit trap", "dhaanto", "dhol tasha", "dhrupad", "digicore",
    "digital cumbia", "digital fusion", "digital hardcore", "dikir barat", "dimotiko",
    "dirty south", "disco", "disco polo", "dissonant black metal", "dissonant death metal",
    "diva house", "divertissement", "dixieland", "djanba", "djent", "doble paso", "dobrado",
    "doina", "dondang sayang", "dongjing", "donk", "donosti sound", "doo-wop", "doom metal",
    "doomcore", "doomgaze", "doskpop", "downtempo", "downtempo deathcore", "dream pop",
    "dream trance", "dreampunk", "drift phonk", "drill", "drill and bass", "drone", "drone metal",
    "drum and bass", "drum and bugle corps", "drumfunk", "drumless hip hop", "drumline",
    "drumstep", "dub", "dub poetry", "dub techno", "dubstep", "dubstyle", "dubwise", "duma",
    "dunedin sound", "dungeon rap", "dungeon sound", "dungeon synth", "duranguense",
    "dutch house", "eai", "early hardstyle", "east coast hip hop", "easy listening", "easycore",
    "ebm", "eccojams", "edm", "electric blues", "electric texas blues", "electro", "electro hop",
    "electro house", "electro latino", "electro swing", "electro-disco", "electro-funk",
    "electro-industrial", "electroacoustic", "electroclash", "electronic", "electronic rock",
    "electronica", "electronicore", "electropop", "electropunk", "electrotango", "eleki",
    "eletrofunk", "embolada", "emo", "emo pop", "emo rap", "emocore", "emoviolence",
    "english pastoral school", "enka", "éntekhno", "epic collage", "epic doom metal", "estrada",
    "ethereal wave", "ethio-jazz", "étude", "euphoric hardstyle", "euro house", "euro-disco",
    "euro-trance", "eurobeat", "eurodance", "europop", "euskal kantagintza berria", "exotica",
    "experimental", "experimental big band", "experimental electronic", "experimental hip hop",
    "experimental rock", "expressionism", "extratone", "fado", "fado de coimbra", "fairy tale",
    "fakaseasea", "falak", "famo", "fandango", "fandango caiçara", "fantasia", "fantezi",
    "festejo", "festival progressive house", "festival trap", "fidget house", "field recording",
    "fife and drum", "fife and drum blues", "fijiri", "filin", "filipino rondalla", "filk",
    "filmi", "finnish tango", "flamenco", "flamenco jazz", "flamenco pop", "flashcore",
    "flex dance music", "florida breaks", "fm synthesis", "folk", "folk metal", "folk pop",
    "folk punk", "folk rock", "folkhop", "folktronica", "fon leb", "football chant", "footwork",
    "footwork jungle", "forest psytrance", "forró", "forró de favela", "forró eletrônico",
    "forró universitário", "frapcore", "frat rap", "frat rock", "freak folk", "freakbeat",
    "free car music", "free folk", "free improvisation", "free jazz", "free tekno",
    "freeform hardcore", "freestyle", "french electro", "french house", "frenchcore", "frevo",
    "frevo de bloco", "frevo de rua", "frevo elétrico", "frevo-canção", "fugue", "fuji", "full-on",
    "funaná", "funeral doom metal", "funeral march", "fungi", "funk", "funk automotivo",
    "funk brasileiro", "funk carioca", "funk de bh", "funk mandelão", "funk melody", "funk metal",
    "funk ostentação", "funk proibidão", "funk rock", "funknejo", "funkot", "funktronica",
    "funky breaks", "funky house", "fusion gugak", "future bass", "future bounce", "future core",
    "future funk", "future garage", "future house", "future rave", "future riddim", "futurepop",
    "futurism", "g-funk", "g-house", "gabber", "gaelic psalm singing", "gagaku", "gagok",
    "gaita zuliana", "gallican chant", "gambang kromong", "gamelan", "gamelan angklung",
    "gamelan beleganjur", "gamelan degung", "gamelan gender wayang", "gamelan gong gede",
    "gamelan gong kebyar", "gamelan jegog", "gamelan joged bumbung", "gamelan salendro",
    "gamelan sekaten", "gamelan selunding", "gamelan semar pegulingan", "gamelan siteran",
    "gamelan surakarta", "gangsta rap", "garage house", "garage psych", "garage punk",
    "garage rock", "garage rock revival", "garba", "geek rock", "género chico",
    "género grande", "genge", "gengetone", "għana", "ghazal", "ghetto funk", "ghetto house",
    "ghettotech", "ginan", "glam", "glam metal", "glam punk", "glam rock", "glitch", "glitch hop",
    "glitch hop edm", "glitch pop", "gnawa", "go-go", "goa trance", "gommance", "gondang",
    "goombay", "goregrind", "gorenoise", "gospel", "gospel house", "gospel reggae", "gothic",
    "gothic country", "gothic metal", "gothic rock", "gqom", "grand opera", "graphical sound",
    "grebo", "gregorian chant", "grime", "grindcore", "griot", "groove metal", "group sounds",
    "grunge", "grupera", "gstanzl", "guaguancó", "guajira", "guangdong yinyue", "guaracha (Cuban)",
    "guaracha edm (Colombian electronic genre)", "guaracha santiagueña", "guarania", "gufeng",
    "guggenmusik", "guided meditation", "guitarrada", "gumbe", "guoyue", "gwo ka", "gypsy jazz",
    "gypsy punk", "habanera", "haitian vodou drumming", "halftime", "hambo", "hamburger schule",
    "hands up", "hanmai", "haozi", "hapa haole", "happy hardcore", "harana", "harawi", "hard beat",
    "hard bop", "hard drum", "hard house", "hard nrg", "hard rock", "hard techno", "hard trance",
    "hard trap", "hardbag", "hardbass", "hardcore breaks", "hardcore hip hop", "hardcore punk",
    "hardcore techno", "hardgroove techno", "hardstep", "hardstyle", "hardvapour", "hardwave",
    "harsh noise", "harsh noise wall", "hát tuồng", "hauntology", "heartland rock", "heaven trap",
    "heavy metal", "heavy psych", "heikyoku", "henan opera", "hexd", "hi-nrg", "hi-tech",
    "hi-tech full-on", "highlife", "hill country blues", "himene tarava", "hindustani classical",
    "hip hop", "hip hop soul", "hip house", "hipco", "hiplife", "holy minimalism", "honky tonk",
    "honkyoku", "hopepunk", "horror punk", "horror synth", "horrorcore", "house", "houston sound",
    "huapango", "huaylarsh", "huayno", "humppa", "hyangak", "hybrid trap",
    "hyper techno (Italo-Japanese 1990s genre)", "hyperpop", "hypertechno (2020s genre)", "hyphy",
    "hypnagogic pop", "iavnana", "idm", "idol kayō", "illbient", "impressionism", "impromptu",
    "indeterminacy", "indian classical", "indian pop", "indie folk", "indie pop", "indie rock",
    "indie surf", "indietronica", "indo jazz", "indorock", "industrial", "industrial hardcore",
    "industrial hip hop", "industrial metal", "industrial musical", "industrial rock",
    "industrial techno", "instrumental", "instrumental hip hop", "instrumental jazz",
    "instrumental rock", "integral serialism", "interview", "iraqi maqam", "irish folk", "isa",
    "isicathamiya", "islamic modal music", "italo dance", "italo house", "italo-disco", "izlan",
    "izvorna bosanska muzika", "j-core", "j-pop", "j-rock", "jácara", "jackin house", "jaipongan",
    "jam band", "jamaican ska", "james bay fiddling", "jamgrass", "jangle pop",
    "japanese classical", "javanese gamelan", "jawaiian", "jazz", "jazz blues", "jazz fusion",
    "jazz guachaca", "jazz house", "jazz mugham", "jazz poetry", "jazz pop", "jazz rap",
    "jazz rock", "jazz-funk", "jazzstep", "jeongak", "jerk (2020s)", "jerk rap (2000s)",
    "jersey club", "jersey club rap", "jersey drill", "jersey sound", "jesus music",
    "jiangnan sizhu", "jit", "jiuta", "joik", "jongo", "joropo", "jōruri", "jota", "jovem guarda",
    "jubilee", "jug band", "jùjú", "juke", "jump blues", "jump up", "jumpstyle", "jungle",
    "jungle dutch", "jungle terror", "junkanoo", "k-pop", "kabarett (German political satire)",
    "kacapi suling", "kadongo kamu", "kafi", "kagura", "kai", "kakawin", "kalattut", "kalindula",
    "kalon'ny fahiny", "kan ha diskan", "kaneka", "kankyō ongaku", "kantan chamorrita",
    "kanto", "kantruem", "kapuka", "kaseko (Suriname)", "kasékò (Guiana)", "kawaii future bass",
    "kawaii metal", "kayōkyoku", "kecak", "keroncong (kroncong)", "kete", "ketuk tilu",
    "khrueang sai", "khyal", "kidandali", "kidumbak", "kilapanga", "kirtan", "kizomba", "klapa",
    "klasik", "kleinkunst", "klezmer", "kliningan", "konnakol", "könsrock", "kontakion", "koplo",
    "korean ballad", "korean classical", "korean revolutionary opera", "kouta", "krakowiak",
    "krautrock", "kréyol djaz", "krushclub", "kuda lumping", "kuduro", "kujawiak", "kulintang",
    "kumi-daiko", "kumiuta", "kundiman", "kunqu", "kwaito", "kwassa kwassa", "kwela",
    "kyivan chant", "laiko", "lambada", "ländlermusik", "landó",
    "langgam jawa", "latin", "latin ballad", "latin disco", "latin funk",
    "latin house", "latin jazz", "latin pop", "latin rock", "latin soul", "lauda", "lavani",
    "lecture", "leftfield", "lento violento", "levenslied", "lied", "liedermacher", "liquid funk",
    "liquid riddim", "liscio", "livetronica", "liwa", "lo-fi", "lo-fi hip hop", "lo-fi house",
    "lolicore", "loner folk", "loud kei", "louisiana blues", "lounge", "lovers rock", "lowend",
    "lowercase", "luk krung", "luk thung", "lullaby", "lundu", "lute song", "mad", "madchester",
    "maddahi", "madrigal", "mafioso rap", "maftirim", "mahori", "mahraganat", "mainstream rock",
    "makina", "makossa", "malagueña venezolana", "malay gamelan", "malhun", "mallsoft",
    "malouf", "maloya", "maloya électronique", "maloya élektrik", "mambo", "mambo chileno",
    "mambo urbano", "mandopop", "manele", "mangambeu", "mangue beat", "manila sound", "mantra",
    "manyao", "marabi", "maracatu", "march", "marching band", "marchinha", "mariachi",
    "marinera", "marrabenta", "martial industrial", "mashcore", "maskanda", "mass", "mataali",
    "math pop", "math rock", "mathcore", "maxixe", "mazurka", "mbalax", "mbaqanga", "mbolé",
    "mbube", "mchiriku", "medieval", "medieval lyric poetry", "medieval metal", "medieval rock",
    "mega funk", "meiji shinkyoku", "melbourne bounce", "melodic bass", "melodic black metal",
    "melodic death metal", "melodic dubstep", "melodic hardcore", "melodic house",
    "melodic metalcore", "melodic techno", "melodic trance", "mélodie", "memphis rap", "mento",
    "menzuma", "merecumbé", "merengue", "merengue típico", "merenhouse", "merequetengue",
    "méringue", "merseybeat", "metal", "metalcore", "métis fiddling", "meyxana", "miami bass",
    "microfunk", "microhouse", "microsound", "microtonal classical", "midtempo bass",
    "midwest emo", "miejski folk", "milonga", "min'yō", "minatory", "mincecore",
    "minimal drum and bass", "minimal synth", "minimal techno", "minimal wave", "minimalism",
    "minneapolis sound", "minstrelsy", "mobb music", "mod", "mod revival", "moda de viola",
    "modal jazz", "modern blues", "modern classical", "modern creative", "modern hardtek",
    "modern laiko", "modinha", "moe song", "monodrama", "mood kayō", "moogsploitation",
    "moombahcore", "moombahton", "mor lam", "mor lam sing", "morenada", "morna", "moroccan chaabi",
    "motet", "motown", "moutya", "movimiento alterado", "mozarabic chant", "mpb", "muak", "mugham",
    "muiñeira", "mulatós", "muliza", "murga", "murga uruguaya", "musette", "music hall",
    "música cebolla", "música criolla", "música de intervenção", "música llanera",
    "música típica chilena", "musical", "mūsīqā lubnāniyya", "musique concrète",
    "musique concrète instrumentale", "muzika mizrahit", "muzika yehudit mekorit",
    "muzikat dika'on", "muziki wa dansi", "nagauta", "nanguan", "narcocorrido",
    "narodnozabavna glasba", "nasheed", "nashville sound", "native american new age",
    "nature sounds", "natya sangeet", "nederbeat", "nederpop", "neo kyma", "neo soul",
    "neo-acoustic", "neo-grime", "neo-medieval folk", "neo-progressive rock", "neo-psychedelia",
    "neo-rockabilly", "néo-trad", "neo-traditional country", "neoclassical dark wave",
    "neoclassical metal", "neoclassical new age", "neoclassicism", "neocrust", "neofolk",
    "neofolklore", "neon pop punk", "neoperreo", "nerdcore", "nerdcore techno",
    "neue deutsche härte", "neue deutsche welle", "neurofunk", "neurohop", "new age", "new beat",
    "new complexity", "new jack swing", "new jazz (trap subgenre)", "new mexico music",
    "new orleans blues", "new orleans r&b", "new rave", "new romantic", "new wave",
    "new york drill", "ngâm thơ", "ngoma", "nhạc đỏ", "nhạc tiền chiến", "nhạc vàng",
    "night full-on", "nightcore", "nigun", "nintendocore", "nitzhonot", "njuup", "no melody trap",
    "no wave", "nocturne", "noh", "noiadance", "noise", "noise pop", "noise rock", "noisecore",
    "noisegrind", "non-music", "nortec", "norteño", "northern soul", "nóta", "nouveau zydeco",
    "nova cançó", "novelty piano", "novo dub", "nu disco", "nu jazz", "nu metal",
    "nu skool breaks", "nu style gabber", "nueva canción", "nueva canción chilena",
    "nueva canción española", "nueva cumbia chilena", "nueva trova", "nuevo cancionero",
    "nuevo flamenco", "nuevo tango", "nustyle", "nwobhm", "nyū myūjikku", "oberek", "occult rock",
    "odissi classical", "ogene music", "oi", "old roman chant", "old school death metal",
    "old school hip hop", "old-time", "omutibo", "onda nueva", "ondō", "onkyo", "opera",
    "opera buffa", "opéra comique", "opera semiseria", "opera seria", "opera-ballet",
    "operatic pop", "operetta", "opm", "oratorio", "orchestral", "orchestral jazz",
    "orchestral song", "organic house", "ori deck", "oriental ballad", "orkes gambus",
    "orthodox pop", "outlaw country", "outsider house", "overture", "özgün müzik", "p-funk",
    "pachanga", "pacific reggae", "pagan black metal", "pagan folk", "paghjella", "pagodão",
    "pagode", "pagode romântico", "paisley underground", "palingsound", "palm-wine",
    "palo de mayo", "pansori", "parang", "parlour music", "partido alto", "pasillo", "pasodoble",
    "passion setting", "payada", "peak time techno", "pep band", "persian classical",
    "persian pop", "philly club", "philly club rap", "philly drill", "philly soul",
    "phleng phuea chiwit", "phonk (older style, a.k.a. rare phonk)", "phonk house", "piano blues",
    "piano rock", "picopop", "piedmont blues", "pigfuck", "pilón", "pimba", "pinpeat",
    "pìobaireachd", "pipe band music", "piphat", "pirekua", "piseiro", "piyyut", "pizzica",
    "plainchant", "plena", "plugg", "pluggnb", "plunderphonics", "poetry",
    "polca criolla (Peruvian polka)", "political hip hop", "polka", "polka paraguaya", "polonaise",
    "pon-chak disco", "pop", "pop ghazal", "pop kreatif", "pop metal", "pop minang", "pop punk",
    "pop raï", "pop rap", "pop rock", "pop soul", "pop yeh-yeh", "porn groove", "pornogrind",
    "porro", "post-bop", "post-britpop", "post-classical", "post-dubstep", "post-grunge",
    "post-hardcore", "post-industrial", "post-metal", "post-minimalism", "post-punk",
    "post-punk revival", "post-rock", "powada", "power electronics", "power metal", "power noise",
    "power pop", "power soca", "powerstomp", "powerviolence", "praise & worship", "praise break",
    "prank calls", "prelude", "process music", "production music", "progressive",
    "progressive bluegrass", "progressive breaks", "progressive country", "progressive electronic",
    "progressive folk", "progressive house", "progressive metal", "progressive metalcore",
    "progressive pop", "progressive psytrance", "progressive rock", "progressive soul",
    "progressive trance", "proto-punk",
    "psichedelia occulta italiana (italian occult psychedelia)", "psybient", "psybreaks",
    "psychedelic", "psychedelic folk", "psychedelic pop", "psychedelic rock", "psychedelic soul",
    "psychobilly", "psychploitation", "psycore", "psystyle", "psytrance", "pub rock",
    "puirt à beul", "pumpcore", "pungmul", "punk", "punk blues", "punk poetry", "punk rap",
    "punk rock", "punta", "punto", "purple sound", "puxa", "q-pop", "qaraami", "qasidah modern",
    "qawwali", "quan họ", "queercore", "quiet storm", "quyi", "r&b", "rabiz", "raga rock", "rage",
    "ragga", "ragga hip-hop", "ragga jungle", "raggacore", "raggatek", "ragtime", "raï",
    "rain sounds", "ranchera", "rap metal", "rap rock", "rapcore", "rapso", "raqs baladi", "rara",
    "rasin", "rasqueado cuiabano", "rasteirinha", "ratchet music", "rautalanka", "rave",
    "raw punk", "rawphoric", "rawstyle", "rebetiko", "red dirt", "red disco", "red song",
    "reductionism", "regalia", "reggae", "reggae rock", "reggae-pop", "reggaeton",
    "regional mexicano", "renaissance", "reparto", "repente", "requiem", "revue", "rhumba",
    "ricercar", "riddim dubstep", "rigsar", "ring shout", "riot grrrl", "ripsaw", "ritmada",
    "ritual ambient", "rizitika", "rkt", "rock", "rock and roll", "rock andaluz",
    "rock andino (andean rock)", "rock musical", "rock opera", "rock rural",
    "rock urbano (español)", "rock urbano mexicano", "rockabilly", "rocksteady", "rōkyoku",
    "rom kbach", "romanian popcorn", "romantic classical", "romantic flow", "romantische oper",
    "rominimal", "roots reggae", "roots rock", "rumba", "rumba catalana",
    "rumba cubana (cuban rumba)", "rumba flamenca", "runo song", "russian chanson",
    "russian orthodox liturgical music", "russian romance", "ryūkōka", "sa'idi", "sacred harp",
    "sacred steel", "saeta", "salegy", "salsa", "salsa choke", "salsa dura", "salsa romántica",
    "saluang klasik", "samba", "samba de breque", "samba de gafieira", "samba de roda",
    "samba de terreiro", "samba soul", "samba-canção", "samba-choro", "samba-enredo",
    "samba-exaltação", "samba-jazz", "samba-joia", "samba-reggae", "samba-rock", "sambalanço",
    "sambass", "sample drill", "sampledelia", "samri", "sanjo", "santé engagé", "sarala gee",
    "sardana", "sarum chant", "sasscore", "sawt", "saya afroboliviana", "scam rap", "schlager",
    "schottische", "schranz", "scottish country dance music", "screamo", "scrumpy and western",
    "sea shanty", "sean-nós", "seapunk", "séga", "seggae", "seguidilla", "seishun punk", "semba",
    "semi-trot", "serenade", "serialism", "sermon", "sertanejo", "sertanejo raiz",
    "sertanejo romântico", "sertanejo universitário", "seto leelo", "sevdalinka", "sevillanas",
    "sexy drill", "shaabi", "shabad kirtan", "shan'ge", "shangaan electro", "shanto", "shashmaqam",
    "shatta", "shibuya-kei", "shidaiqu", "shima-uta", "shinkyoku", "shitgaze", "shoegaze",
    "shōmyō", "shoor", "sichuan opera", "sierreño", "sigidrigi", "sigilkore", "sinawi",
    "sinfonia concertante", "singeli", "singer-songwriter", "singspiel", "sissy bounce",
    "sitarsploitation", "sizhu music", "ska", "ska punk", "skacore", "skate punk", "sketch comedy",
    "skiffle", "skiladiko", "skinhead reggae", "skullstep", "skweee", "slack-key guitar",
    "slacker rock", "slam death metal", "slam poetry", "slap house", "sleaze rock", "slimepunk",
    "slow waltz", "slowcore", "sludge metal", "slushwave", "smooth jazz", "smooth soul",
    "snap", "soca", "soft rock", "sōkyoku", "son calentano", "son cubano", "son de pascua",
    "son huasteco", "son istmeño", "son jarocho", "son montuno", "son nica", "sonata", "songo",
    "sonorism", "sophisti-pop", "soukous", "soul", "soul blues", "soul jazz", "sound art",
    "sound collage", "sound effects", "sound poetry", "southeast asian classical",
    "southern gospel", "southern hip hop", "southern metal", "southern rock", "southern soul",
    "sovietwave", "space age pop", "space ambient", "space disco", "space rock",
    "space rock revival", "spacesynth", "spamwave", "spectralism", "speech", "speed garage",
    "speed house", "speed metal", "speedcore", "spiritual jazz", "spirituals", "splittercore",
    "spoken word", "spouge", "staïfi", "standup comedy", "steampunk", "steel band",
    "stenchcore", "sticheron", "stochastic music", "stomp and holler", "stoner metal",
    "stoner rock", "stornello", "street punk", "stride", "string quartet", "stutter house",
    "sufi rock", "sufiana kalam", "sundanese pop", "sungura", "sunshine pop", "suomisaundi",
    "surf", "surf punk", "surf rock", "sutartinės", "swamp blues", "swamp pop", "swamp rock",
    "swancore", "swing", "swing revival", "symphonic black metal", "symphonic metal",
    "symphonic mugham", "symphonic poem", "symphonic prog", "symphonic rock", "symphony",
    "synth funk", "synth-pop", "synthwave", "t-pop", "taarab", "tajaraste", "takamba", "talempong",
    "talempong goyang", "talking blues", "tallava", "tamborera", "tamborito", "tamborzão",
    "tammurriata", "tân cổ giao duyên", "tango", "tanjidor", "taoist ritual music", "tape music",
    "tappa", "taquirari", "tarana", "tarantella", "tarawangsa", "tarraxinha", "tassa", "tassu",
    "tchinkoumé", "tearout (older dubstep subgenre)", "tearout brostep", "tech house",
    "tech trance", "technical death metal", "technical thrash metal", "techno", "techno bass",
    "techno kayō", "technobanda", "techstep", "tecnobrega", "tecnofunk", "tecnomerengue",
    "tecnorumba", "teen pop", "tejano", "tembang cianjuran", "terror plugg", "terrorcore",
    "tex-mex", "texas blues", "texas country", "thai classical", "thall", "theme and variations",
    "third stream", "third wave ska", "thrash metal", "thrashcore", "thumri",
    "tibetan buddhist chant", "tiento", "timba", "timbila", "tin pan alley", "tivaner inngernerlu",
    "tizita", "toada de boi", "toccata", "tonada asturiana", "tonada potosina", "tonadilla",
    "tondero", "tontipop", "totalism", "township bubblegum", "township jive", "toypop",
    "toytown pop", "tradi-moderne congolais", "tradi-moderne ivoirien", "traditional black gospel",
    "traditional bluegrass", "traditional country", "traditional doom metal", "traditional pop",
    "tragédie en musique", "trallalero", "trampská hudba", "trance", "trance metal", "trancestep",
    "trap", "trap edm", "trap latino (latin trap)", "trap metal", "trap shaabi", "trap soul",
    "trapfunk", "tread", "tribal ambient", "tribal guarachero", "tribal house", "trikitixa",
    "trip hop", "troparion", "tropical house", "tropical rock", "tropicália", "tropicanibalismo",
    "tropipop", "trot", "trova", "trova yucateca", "truck driving country", "tsapiky",
    "tsonga disco", "tsugaru-jamisen", "tumba", "tumba francesa", "tumbélé", "turbo-folk",
    "turkish classical", "turntablism", "twee pop", "twerk", "twoubadou", "uaajeerneq",
    "udigrudi", "uk drill", "uk funky", "uk garage", "uk hardcore", "uk jackin", "uk street soul",
    "uk82", "unakesa", "underground hip hop", "unyago", "upopo", "uptempo hardcore",
    "urban contemporary gospel", "urban cowboy", "urtiin duu", "urumi melam", "us power metal",
    "utopian virtual", "uyghur muqam", "uzun hava", "v-pop", "vaigat", "vallenato", "vals criollo",
    "vals venezolano", "valsa brasileira", "vanera", "vapornoise", "vaportrap", "vaporwave",
    "vaudeville", "vaudeville blues", "vedic chant", "verbunkos", "verismo", "vietnamese bolero",
    "vietnamese classical", "viking metal", "viking rock", "villancico", "vinahouse", "visa",
    "visual kei", "vocal house", "vocal jazz", "vocal surf", "vocal trance", "vocalese",
    "volkstümliche musik", "vude", "wa euro", "waka", "waltz", "wangga", "war metal", "wassoulou",
    "waulking song", "wave", "weightless", "west coast breaks", "west coast hip hop",
    "west coast swing", "western (cowboy/western country)", "western classical", "western swing",
    "whale song", "whistling", "white voice", "winter synth", "witch house", "wong shadow",
    "wonky", "wonky techno", "work song", "world fusion", "worldbeat", "wyrd folk", "xẩm",
    "xaxado", "xian psych", "xote", "xuc", "yacht rock", "yakousei", "yangzhou opera", "yaraví",
    "yayue", "yé-yé", "yodeling", "ytpmv", "yu-mex", "yue opera", "yukar", "zamacueca", "zamba",
    "zamrock", "zarzuela", "zarzuela barroca (baroque zarzuela)", "zeitoper", "zema", "zenonesque",
    "zess", "zeuhl", "zeybek", "zhongguo feng", "ziglibithy", "zinli", "znamenny chant", "zoblazo",
    "zohioliin duu", "zolo", "zouglou", "zouk", "zouk love", "zydeco"]


class HelpMenu(ModalScreen):

    BINDINGS = [("q", "quit_menu", "Quit Menu")]

    CSS_PATH = "css/editInputHelpMenu.tcss"

    def compose(self) -> ComposeResult:
        yield Static(
            textwrap.dedent("""
                This Is The Menu That You Will Use To Edit Metadata. Just Input Your Data Into The
                Text Boxes And Then Check Which Playlists It Should Go Into. Once Done Hit The All
                Done! Button. Below Is A Specification List For The Metadata Fields:

                Title: Title Of Song
                Artists: Comma Delimited List Of Artists
                Duration: Duration In Seconds
                Album Date: Date Of Album Release. Must be in the form YYYY-MM-DD
                Album Length: Amount Of Tracks In Album
                Track Number: Number Of Current Track
                Thumbnail Link: Link Of Thumbnail


                Press q To Exit This Help Menu
                """), id="EditHelpStatic")

    def action_quit_menu(self):
        tui_log("Quit menu dismissing")
        self.dismiss()


class EditInputMenu(ModalScreen[MetadataCtx]):

    MAX_GENRE_AMT = 3
    DATE_FORMAT = "%Y-%m-%d"
    CSS_PATH = "css/editInput.tcss"
    BINDINGS = [("ctrl+h", "help_menu", "Help Menu")]

    def __init__(self, metadata: dict, type: str):

        self.metadata = metadata[type]
        self.output = MetadataCtx()
        self.output.path = self.app.report_dict[self.app.current_report_key]["pre"]["path"]

        self.default_validator = [Function(self.validator_is_empty, "Is Empty")]
        self.album_len_validator = self.default_validator + [Number(minimum=1)]
        self.image_validator = self.default_validator + [Function(self.validator_is_valid_image,
                                                                  "Invalid URL")]
        self.date_validator = self.default_validator + [Function(self.validator_is_valid_date,
                                                                 "Invalid Date Format")]
        self.track_num_validator = self.default_validator + [
            Function(self.validator_is_valid_track, "Is Invalid")
        ]

        super().__init__()
        tui_log(f"Edit input menu metadata: {self.metadata}")

    @work
    async def action_help_menu(self):
        tui_log("Help menu called")
        await self.app.push_screen(HelpMenu(), wait_for_dismiss=True)

    def convert_for_input(self, value):
        if (value):
            return str(value)
        else:
            return None

    def compose(self) -> ComposeResult:

        tui_log("Compose Started")

        pre = self.app.report_dict[self.app.current_report_key]["pre"]

        with VerticalScroll(id="InputMenuScrollContainer", can_focus=True):
            yield Label("Title", classes="EditPageLabel")
            yield Input(placeholder="Name of Song", value=self.metadata["title"],
                        type="text", id="title", validators=self.default_validator,
                        classes="EditPageInput")

            yield Label("Artist", classes="EditPageLabel")
            yield Input(placeholder="Main Artist", value=self.metadata.get("artist", None),
                        type="text", id="artist", validators=self.default_validator,
                        classes="EditPageInput")

            # TODO: the contents of this will always have the artist content in the beginning so
            #       fill this in for the user ~ BEF
            yield Label("Artists", classes="EditPageLabel")
            yield Input(placeholder="Comma Delimited List Of All Artists Involved **Including** "
                        "The Main Artist",
                        value=list_to_comma_str(self.metadata.get("artists", None)),
                        type="text", id="artists", validators=self.default_validator,
                        classes="EditPageInput")

            yield Label("Duration", classes="EditPageLabel")
            yield Input(placeholder="Duration Of Song In Seconds",
                        value=self.convert_for_input(pre.get("duration", None)), type="integer",
                        id="duration", validators=self.default_validator,
                        classes="EditPageInput")

            yield Label("Album Date", classes="EditPageLabel")
            yield Input(placeholder="YYYY-MM-DD", type="text", id="album_date",
                        validators=self.date_validator, classes="EditPageInput")

            yield Label("Album", classes="EditPageLabel")
            yield Input(placeholder="Album Name Or Song Name If Single",
                        value=self.metadata.get("album", None), type="text", id="album",
                        validators=self.default_validator, classes="EditPageInput")

            yield Label("Album Length", classes="EditPageLabel")
            yield Input(placeholder="Amount Of Tracks In Album", type="integer",
                        value=self.convert_for_input(self.metadata.get("total_tracks", None)),
                        id="album_len", validators=self.album_len_validator,
                        classes="EditPageInput")

            yield Label("Track Number", classes="EditPageLabel")
            yield Input(placeholder="This Song's Track Number Within Album",
                        value=self.convert_for_input(self.metadata.get("track_num", None)),
                        type="integer", id="track_num", validators=self.track_num_validator,
                        classes="EditPageInput")

            yield Label("Genres", classes="EditPageLabel")
            # TO-DO: yeahhh...lets fix this please ~ BEF
            # TO-DO: just allow non musicbrainz genres and maybe clean them up with ending
            #        whitespace and all lowercase. This mapping thing is stupid ~ BEF
            for i in range(0, self.MAX_GENRE_AMT):
                if (self.metadata.get("genres", None)):
                    if ((i < len(self.metadata["genres"]))
                            and (self.metadata["genres"][i])):
                        if (self.metadata["genres"][i] in MUSICBRAINZ_GENRES):
                            select_value = (self.metadata["genres"][i], self.metadata["genres"][i])
                        else:
                            select_value = self.get_musicbrainz_mapping(self.metadata["genres"][i])
                    else:
                        select_value = Select.BLANK
                else:
                    select_value = Select.BLANK

                yield Select(((line, line) for line in MUSICBRAINZ_GENRES), value=select_value,
                             classes="EditPageListItem", prompt=f"Genre {i+1}")

            yield Label("Thumbnail Link", classes="EditPageLabel")
            yield Input(placeholder="Link To Thumbnail",
                        value=self.metadata.get("thumbnail_url", None), type="text",
                        id="thumb_link", validators=self.image_validator, classes="EditPageInput")

            preview_image = initialize_image("EditInputUrlPreview")
            yield preview_image
            self._obtain_image(self.metadata.get("thumbnail_url", None), preview_image)

            for playlist in self.app.playlist_handler.list_playlists_str():
                if (playlist in [play[1] for play in pre["playlists"]]):
                    yield Checkbox(playlist, True, name=playlist, classes="EditPageCheckbox")
                else:
                    yield Checkbox(playlist, False, name=playlist, classes="EditPageCheckbox")

        yield Button("All Done!", variant="primary", id="completion_button")
        # TO-DO: change this to self.app.notify ~ BEF
        yield Static("", disabled=True, id="EditInputErr")

        yield Footer()
        tui_log("Compose completed")

    def get_musicbrainz_mapping(self, input: str):
        """ Get Musicbrainz genre name from Soundcloud name. """
        mb_genre = next((mapping[1] for mapping in SOUNDCLOUD_GENRES if input == mapping[0]), None)
        if (not mb_genre):
            raise ValueError(f"Genre {input} not known. Please add a mapping for it.")
        return (mb_genre)

    def validator_is_empty(self, value) -> bool:
        if (value):
            return (True)
        else:
            return (False)

    def validator_is_valid_image(self, image_url: str) -> bool:

        try:
            with urllib.request.urlopen(image_url) as response:
                if response.status == 200:
                    type = response.headers.get("Content-Type")
                    if type and type.startswith("image"):
                        return True
        except (urllib.error.URLError, ValueError):
            return False

    def validator_is_valid_track(self, value) -> bool:
        try:
            album_len = self.query_one("#album_len", Input)

            if (album_len and value and
                    (int(value) > 0) and
                    (int(album_len.value) >= int(value))):
                return True

        except ValueError:
            return False
        except NoMatches:
            # NOTE: Ordering matters here. Album length is loaded after track number therefore it
            #       doesn't exist the first time around. ~ BEF
            return True

    def validator_is_valid_date(self, value) -> bool:
        output = False
        try:
            output = bool(datetime.strptime(value, self.DATE_FORMAT))
        except ValueError:
            pass

        return output

    def validate_all(self, container):
        tui_log("Validating all children")
        for widget in container.children:
            if hasattr(widget, "validate") and callable(widget.validate):
                tui_log(widget.validate(widget.value))

    def check_input_validity(self) -> bool:

        # NOTE: Even though not needed we validate all to update borders ~ BEF
        container = self.query_one("#InputMenuScrollContainer", VerticalScroll)
        self.validate_all(container)
        err_static = self.query_one("#EditInputErr", Static)
        input_widgets = [widget for widget in container.children if isinstance(widget, Input)]
        for widget in input_widgets:
            if (not widget.is_valid):
                err_static.disabled = False
                for validator in widget.validators:
                    if (validator.failure_description):
                        err_static.update(Content(f'"{widget.id}" {
                            validator.failure_description}'))
                return False
        return True

    def on_select_changed(self, event: Select.Changed) -> None:
        # NOTE: When a select is changed we will just update the entire genre list to avoid having
        #       to keep track of the indices~ BEF
        for select in self.query("Select"):
            if (not (Select.BLANK == select.value)):
                self.output.genres.append(select.value)

    def on_input_blurred(self, blurred_widget):

        if (blurred_widget.input.id == "thumb_link"):
            preview_image = self.query_one("#EditInputUrlPreview", Image)
            if (blurred_widget.input.is_valid):
                dimensions = get_img_size_url(blurred_widget.value)
                self.output.thumbnail_url = blurred_widget.value
                self.output.thumbnail_width = dimensions[0]
                self.output.thumbnail_height = dimensions[1]

                preview_image.loading = True
                self._obtain_image(blurred_widget.value, preview_image)
            else:
                preview_image.image = FAILURE_IMAGE_PATH

        elif (not (blurred_widget.input.id == "artists")):
            if (not blurred_widget.input.type == "integer"):
                setattr(self.output, blurred_widget.input.id, blurred_widget.value)
            else:
                setattr(self.output, blurred_widget.input.id,
                        None if not blurred_widget.value else int(blurred_widget.value))
        else:
            setattr(self.output, blurred_widget.input.id, comma_str_to_list(blurred_widget.value))

    def on_checkbox_changed(self, changed_checkbox):

        playlist = self.app.playlist_handler.get_playlist_tuple(changed_checkbox.checkbox.name)

        if (changed_checkbox.value and
                (not (playlist in self.output.playlists))):
            tui_log(f"Adding playlist: {playlist}")
            self.output.playlists.append(playlist)
        elif ((not changed_checkbox.value) and (playlist in self.output.playlists)):
            tui_log(f"Removing playlist: {playlist}")
            self.output.playlists.remove(playlist)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if (not self.check_input_validity()):
            return
        tui_log("Exiting input menu")
        self.dismiss(self.output)

    @work
    async def _obtain_image(self, url: str, image: Image):
        await obtain_image_from_url(url, image)

    def on_mount(self) -> None:
        container = self.query_one("#InputMenuScrollContainer", VerticalScroll)
        self.validate_all(container)


class EditSelectionMenu(ModalScreen):

    CSS_PATH = "css/editSelection.tcss"

    BINDINGS = [
        ("q", "quit_menu", "Quit Menu"),
        ("escape", "quit_menu", "Quit Menu"),
    ]

    def __init__(self):
        """ Initialize Edit Metadata Screen """
        self.meta_type_chosen = None
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Which Metadata Would You Like To Edit?", id="EditSelectionLabel"),
            Button("Pre", variant="primary", id="EditSelectionButtonPre"),
            Button("Post", variant="success", id="EditSelectionButtonPost"),
            id="EditSelectionGrid"
        )

    def action_quit_menu(self):
        self.dismiss(None)

    def on_button_pressed(self, event: Button.Pressed):
        if (event.button.id == "EditSelectionButtonPre"):
            self.meta_type_chosen = "pre"
        else:
            self.meta_type_chosen = "post"

        self.dismiss(self.meta_type_chosen)


class ctl_tui(App):

    REQUIRED_POST_SEARCH_KEYS = ["title", "artist", "artists", "track_num", "total_tracks",
                                 "release_date", "thumbnail_url", "thumbnail_width",
                                 "thumbnail_height"]
    BINDINGS = [
        ("n", "accept_new", "Accept New Metadata"),
        ("o", "accept_original", "Accept Original"),
        ("e", "edit_metadata", "Edit Metadata"),
        # ("s", "search_again", "Search Again"),
        # ("r", "replace_entry", "Retry Download Process With New URL"),
        ("ctrl+s", "skip_entry", "Skip Entry"),
        # ("ctrl+r", "retry_download", "Retry Download Process"),
        # ("p", "pick_and_choose", "Pick Elements To Pick From Both Before And After")
    ]
    CSS_PATH = "css/main.tcss"

    # Refresh Footer/Bindings and recompose on change
    current_report_key = reactive(None, recompose=True, bindings=True)

    def __init__(self, arguments, **kwargs):
        super().__init__(**kwargs)

        self.theme = "textual-dark"
        self.outdir = arguments.outdir
        self.report_path = self.outdir+"ctl_report"

        self.playlists_info = []
        self.playlist_handler = PlaylistHandler(arguments.retry_amt,
                                                arguments.playlists,
                                                self.playlists_info,
                                                arguments.request_sleep)

        with open(self.report_path, "r") as fptr:
            self.report_dict = json.load(fptr)
        self.current_report_key_iter = iter(list(self.report_dict))
        self.current_report_key = next(self.current_report_key_iter)

    def pop_and_increment_report_key(self):
        try:
            self.report_dict.pop(self.current_report_key)
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            tui_log("All songs in report exhausted")
            with open(self.report_path, "w") as f:
                json.dump(self.report_dict, f, indent=2)
            self.exit()

    def increment_report_key(self):
        try:
            self.current_report_key = next(self.current_report_key_iter)
        except StopIteration:
            tui_log("All songs in report exhausted")
            with open(self.report_path, "w") as f:
                json.dump(self.report_dict, f, indent=2)
            self.exit()

    def _get_current_report(self) -> dict:
        return (self.report_dict[self.current_report_key])

    def compose(self) -> ComposeResult:

        title = None
        pre_height = None
        post_width = None
        post_height = None
        current_report = self._get_current_report()

        if (ReportStatus.DOWNLOAD_FAILURE == current_report["status"]):
            title = "Download Failed"
            yield Horizontal(Image(FAILURE_IMAGE_PATH, id="full_img"), id="album_art")
            info_content = [
                Static(get_report_status_str(
                    current_report["status"]), id="status"),
            ]
        else:
            pre_width = current_report["pre"]["thumbnail_width"]
            pre_height = current_report["pre"]["thumbnail_height"]

            if (current_report["status"] in [ReportStatus.SINGLE, ReportStatus.ALBUM_FOUND]):

                pre_image = initialize_image("pre_image")
                post_image = initialize_image("post_image")

                yield Horizontal(pre_image, post_image, id="album_art")

                self._obtain_image(current_report["pre"]["thumbnail_url"], pre_image)
                self._obtain_image(current_report["post"]["thumbnail_url"], post_image)

                title = current_report["post"]["title"]
                post_width = current_report["post"]["thumbnail_width"]
                post_height = current_report["post"]["thumbnail_height"]

                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Horizontal(
                        Pretty(current_report["pre"], id="pre_info"),
                        Container(id="spacer"),
                        Pretty(current_report["post"], id="post_info"),
                        id="album_content"
                    )
                ]

            elif (current_report["status"] == ReportStatus.METADATA_NOT_FOUND):
                pre_image = initialize_image("full_img")
                yield Horizontal(pre_image, id="album_art")
                self._obtain_image(current_report["pre"]["thumbnail_url"], pre_image)

                title = current_report["pre"]["title"]
                post_width = None
                info_content = [
                    Static(get_report_status_str(
                        current_report["status"]), id="status"),
                    Pretty(current_report["pre"], id="pre_info")
                ]
            # TODO: you can cut a download off to end up at download failure for the report status
            #       which will cause this to fail. Allow user to redownload in this case ~ BEF

        post_dimension_str = "(X,X)" if not post_width else f"({post_width}px, {post_height}px)"
        pre_dimension_str = "(X,X)" if not pre_width else f"({pre_width}px, {pre_height}px)"
        self.title = f"{pre_dimension_str} {title} {post_dimension_str}"

        yield Header()
        yield Rule(line_style="ascii", id="divider")
        with Container(id="album_info"):
            for content in info_content:
                yield content
        yield Footer()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:

        disabled_action_list = ["command_palette"]
        match (self._get_current_report()["status"]):
            case ReportStatus.DOWNLOAD_FAILURE:
                disabled_action_list += ["accept_new", "accept_original", "edit_metadata"]
            case ReportStatus.DOWNLOAD_SUCCESS:
                disabled_action_list += ["accept_new"]
            case ReportStatus.METADATA_NOT_FOUND:
                disabled_action_list += ["accept_new"]
            case ReportStatus.SINGLE:
                disabled_action_list += []
            case ReportStatus.ALBUM_FOUND:
                disabled_action_list += []

        if (action in disabled_action_list):
            return False
        return True

    @work
    async def action_accept_original(self):

        await self.push_screen(EditInputMenu(self._get_current_report(), "pre"),
                               self.complete_edit_of_metadata,
                               wait_for_dismiss=True)

    @work
    async def action_edit_metadata(self) -> None:
        if (not ("post" in self._get_current_report())):
            await self.push_screen(EditInputMenu(self._get_current_report(), "pre"),
                                   self.complete_edit_of_metadata,
                                   wait_for_dismiss=True)
        else:
            selected_type = await self.push_screen(EditSelectionMenu(),
                                                   wait_for_dismiss=True)

            if (selected_type):
                await self.push_screen(EditInputMenu(self._get_current_report(),
                                                     selected_type),
                                       self.complete_edit_of_metadata,
                                       wait_for_dismiss=True)

    # TO-DO: create new screen for this

    def action_search_again(self):
        pass
        self.playlist_handler.write_to_playlists()
        self.pop_and_increment_report_key()

    # TO-DO: create new screen for this
    def action_replace_entry(self):
        pass
        self.playlist_handler.write_to_playlists()
        self.pop_and_increment_report_key()

    def action_skip_entry(self):
        self.increment_report_key()

    def complete_edit_of_metadata(self, meta_ctx: MetadataCtx):

        replace_metadata(meta_ctx)

        self.playlist_handler.write_to_playlists(meta_ctx, self.outdir, None)

        self.pop_and_increment_report_key()

    @work
    async def action_accept_new(self):
        """ Accept newly written metadata
            @note currently metadata is written when new album is found with confidence, so this
            doesn't need to do anything"""

        current_report = self._get_current_report()

        if (not all(
                ((key in current_report["post"]) and current_report["post"][key] is not None)
                for key in self.REQUIRED_POST_SEARCH_KEYS)):
            await self.push_screen(EditInputMenu(current_report, "post"),
                                   self.complete_edit_of_metadata,
                                   wait_for_dismiss=True)

        else:

            pre = current_report["pre"]
            post = current_report["post"]
            meta = MetadataCtx(title=post["title"],
                               artist=post["artist"],
                               artists=post["artists"],
                               path=pre["path"],
                               album=post["album"],
                               duration=pre["duration"],
                               track_num=post["track_num"],
                               album_len=post["total_tracks"],
                               album_date=post["release_date"],
                               thumbnail_url=post["thumbnail_url"],
                               thumbnail_width=post["thumbnail_width"],
                               thumbnail_height=post["thumbnail_height"],
                               playlists=pre["playlists"]
                               )

            self.complete_edit_of_metadata(meta)

    # TO-DO: create new screen for this
    def action_retry_download(self):
        pass
        self.pop_and_increment_report_key()

    def action_pick_and_choose(self):
        pass
        self.pop_and_increment_report_key()

    def action_quit(self):
        tui_log("Exiting TUI")
        with open(self.report_path, "w") as f:
            json.dump(self.report_dict, f, indent=2)
        self.exit()

    @work
    async def _obtain_image(self, url: str, image: Image):

        await obtain_image_from_url(url, image)
