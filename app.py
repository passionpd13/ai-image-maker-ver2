import streamlit as st
import random
import time
import os
import re
import shutil
import zipfile
import gc
import uuid
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from google import genai
from google.genai import types

# ==========================================
# [설정] 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="열정피디 AI 이미지 생성기 VER.2 (Final)",
    layout="wide",
    page_icon="🎨",
    initial_sidebar_state="expanded"
)

# 사용자별 고유 세션 ID 생성
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

# ==========================================
# [디자인] 다크모드 & 가독성 완벽 패치
# ==========================================
st.markdown("""
    <style>
    /* 1. 상단 헤더 */
    header[data-testid="stHeader"] {
        background-color: #0E1117 !important;
        z-index: 1 !important;
    }

    /* 2. 콘텐츠 영역 여백 */
    .block-container {
        padding-top: 6rem !important; 
        padding-bottom: 5rem !important;
    }

    /* 3. 전체 배경 및 폰트 */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF !important;
        font-family: 'Pretendard', sans-serif;
    }

    /* 텍스트 가독성 강화 */
    p, div, label, span, li, h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    h1, h2 {
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    /* 4. 배너 스타일 */
    .student-banner {
        background: linear-gradient(90deg, #00C6FF 0%, #0072FF 100%);
        color: white !important;
        padding: 30px 20px;
        border-radius: 15px;
        text-align: center;
        font-size: 2.0rem;
        font-weight: 800;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        letter-spacing: 1px;
    }

    /* 5. 입력창 스타일 */
    .stTextInput label p, .stTextArea label p, .stSelectbox label p, .stRadio label p {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #FFD700 !important;
        margin-bottom: 8px !important;
    }

    .stTextInput input, .stTextArea textarea {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
        border: 1px solid #4A4A4A !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0072FF !important;
        box-shadow: 0 0 8px rgba(0, 114, 255, 0.5);
    }

    /* 6. Selectbox 스타일 */
    div[data-testid="stSelectbox"] > div > div {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
        border: 1px solid #4A4A4A !important;
    }
    div[data-testid="stSelectbox"] * {
        color: #FFFFFF !important;
    }
    div[data-testid="stSelectbox"] svg {
        fill: #FFFFFF !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-testid="stSelectboxVirtualDropdown"] {
        background-color: #1F2128 !important;
    }
    li[role="option"] {
        color: #FFFFFF !important;
        background-color: #1F2128 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #333 !important;
        color: #00BFFF !important; 
    }

    /* 7. 버튼 스타일 */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%);
        color: white !important;
        border: none;
        padding: 15px 20px;
        font-size: 1.2rem !important;
        font-weight: bold;
        border-radius: 10px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 5px 15px rgba(255, 75, 43, 0.4);
    }

    [data-testid="stDownloadButton"] button {
        background-color: #2C2F38 !important;
        border: 1px solid #555 !important;
        color: white !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        border-color: #00BFFF !important;
        color: #00BFFF !important;
    }

    /* 8. Expander 스타일 */
    div[data-testid="stExpander"] details {
        background-color: #1F2128 !important;
        border: 1px solid #4A4A4A !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stExpander"] details > summary {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stExpander"] details > summary:hover {
        background-color: #2C2F38 !important;
        color: #FFD700 !important;
    }
    div[data-testid="stExpander"] details > summary span {
        color: inherit !important;
    }
    div[data-testid="stExpander"] details > summary svg {
        fill: #FFFFFF !important;
    }
    div[data-testid="stExpander"] details > summary:hover svg {
        fill: #FFD700 !important;
    }
    div[data-testid="stExpander"] details > div {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
    }
    
    /* 9. Status Widget 스타일 */
    div[data-testid="stStatusWidget"] {
        background-color: #1F2128 !important;
        border: 1px solid #4A4A4A !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stStatusWidget"] p, 
    div[data-testid="stStatusWidget"] span, 
    div[data-testid="stStatusWidget"] div, 
    div[data-testid="stStatusWidget"] label {
        color: #FFFFFF !important;
    }
    div[data-testid="stStatusWidget"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: #12141C;
        border-right: 1px solid #2C2F38;
    }
    </style>

    <div class="student-banner">
        🎨 열정피디 AI 이미지 생성기 (Final)
    </div>
""", unsafe_allow_html=True)

# 파일 저장 경로
BASE_PATH = "./web_result_files"

# ==========================================
# [함수] 1. 유틸리티
# ==========================================
def split_script_by_time(script, chars_per_chunk=100):
    temp_sentences = script.replace(".", ".|").replace("?", "?|").replace("!", "!|").split("|")
    chunks = []
    current_chunk = ""
    MIN_LENGTH = 30 

    for sentence in temp_sentences:
        sentence = sentence.strip()
        if not sentence: continue
        
        if current_chunk:
            temp_combined = current_chunk + " " + sentence
        else:
            temp_combined = sentence

        if len(temp_combined) < chars_per_chunk:
            current_chunk = temp_combined
        else:
            if len(current_chunk) < MIN_LENGTH:
                current_chunk = temp_combined
            else:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
    
    if current_chunk.strip():
        if len(current_chunk) < MIN_LENGTH and chunks:
            chunks[-1] += " " + current_chunk.strip()
        else:
            chunks.append(current_chunk.strip())
            
    return chunks

def make_filename(scene_num, text_chunk):
    clean_line = text_chunk.replace("\n", " ").strip()
    clean_line = re.sub(r'[\\/:*?"<>|]', "", clean_line)
    words = clean_line.split()
    if len(words) <= 6:
        summary = " ".join(words)
    else:
        summary = f"{' '.join(words[:3])}...{' '.join(words[-3:])}"
    return f"S{scene_num:03d}_{summary}.png"

def create_zip_buffer(source_dir):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.basename(file_path))
    buffer.seek(0)
    return buffer

# ==========================================
# [함수] 2. 프롬프트 생성
# ==========================================
def generate_prompt(api_key, index, text_chunk, style_instruction, video_title, genre_mode="info", target_language="Korean"):
    scene_num = index + 1
    client = genai.Client(api_key=api_key)

    # 1. 언어 설정
    if target_language == "Korean":
        lang_guide = "화면 속 글씨는 **무조건 '한글(Korean)'로 표기**하십시오. (다른 언어 절대 금지)"
        lang_example = "(예: 'New York' -> '뉴욕', 'Tokyo' -> '도쿄')"
    elif target_language == "English":
        lang_guide = "화면 속 글씨는 **무조건 '영어(English)'로 표기**하십시오."
        lang_example = "(예: '서울' -> 'Seoul', '독도' -> 'Dokdo')"
    elif target_language == "Japanese":
        lang_guide = "화면 속 글씨는 **무조건 '일본어(Japanese)'로 표기**하십시오."
        lang_example = "(예: '서울' -> 'ソウル', 'New York' -> 'ニューヨーク')"
    else:
        lang_guide = f"화면 속 글씨는 **무조건 '{target_language}'로 표기**하십시오."
        lang_example = ""

    # 2. 장르별 프롬프트 분기
    if genre_mode == "history":
        full_instruction = f"""
    [역할]
    당신은 **세계사의 결정적인 순간들(한국사, 서양사, 동양사 등)**을 한국 시청자에게 전달하는 '시대극 애니메이션 감독'입니다.
    역사적 비극을 다루지만, 절대로 잔인하거나 혐오스러운 묘사를 하지 않습니다.

    [전체 영상 주제] "{video_title}"
    [그림 스타일 가이드 - 유저 지정 (최우선 준수)] {style_instruction}
    
    [필수 연출 지침]
    1. **[매우 중요] 매체(Medium):** 무조건 **평면적인 '2D 스틱맨 일러스트레이션'** 스타일로 표현하십시오. (3D, 실사, 모델링 느낌 절대 금지)
    2. **[매우 중요] 텍스트 현지화(Localization):** 배경이 서양, 중국, 일본 등 어디든 상관없이, {lang_guide}
        - **금지:** 지정된 언어 외의 문자 사용을 절대 금지합니다.
        - **예시:** {lang_example}
    3. **[매우 중요 - 순화된 표현] 비극의 상징화(Symbolization of Tragedy):** 전쟁, 죽음, 고통과 같은 비극적인 상황은 **절대로 직접적으로 묘사하지 마십시오.** 물리적 폭력 대신, **상실감, 허무함, 애도**의 정서에 집중하십시오.
        - **핵심:** 파괴된 신체나 직접적인 무기 사용 장면 대신, **남겨진 물건(주인 없는 신발, 깨진 안경), 드리우는 그림자, 시들어버린 자연물, 혹은 빛이 사라지는 연출** 등을 통해 간접적으로 슬픔을 표현하십시오.
    4. **[핵심] 다양한 장소와 시대 연출(Diverse Locations):** 대본에 나오는 **특정 시대와 장소의 특징(건축 양식, 의상, 자연환경)을 정확히 포착**하여 그리십시오.
    5. **[수정됨] 절제된 캐릭터 연기(Restrained Acting):** 2D 스틱맨 캐릭터는 시대에 맞는 의상을 입되, **과장된 표정보다는 '몸짓(Body Language)'과 '분위기'로 감정을 표현**해야 합니다. 비극적인 상황에서도 격렬한 분노나 공포보다는 **깊은 슬픔, 체념, 혹은 간절한 기도**와 같은 정적인 감정을 우선시하십시오.
    6. **조명(Lighting):** 2D 작화 내에서 극적인 분위기를 만드는 **'시네마틱 조명'**을 사용하십시오. (시대극 특유의 톤)
    7. **[수정됨] 색감(Colors):** **차분하고 애상적인 색감(Somber & Melancholic Tones)**을 사용하십시오. 깊이 있되 다양한 채도의 색조를 사용하여, 역사 다큐멘터리의 톤앤매너를 유지하십시오. (자극적인 붉은색 과다 사용 금지)
    8. **구성(Composition):** 시청자가 상황을 한눈에 이해할 수 있도록 핵심 피사체를 화면 중앙에 배치하십시오. 분활화면(Split screen)은 금지입니다.
    - **[절대 금지]:** 텍스트가 화면의 네 모서리(Corners)나 가장자리에 배치되는 것을 절대 금지합니다. (자막 공간 확보)
    9. **[매우 중요] 배경보다 **'인물(Character)'이 무조건 우선**입니다. 캐릭터가 화면을 장악해야 합니다.
    10. 상호작용하는 소품 (Interactive Props): 스틱맨 캐릭터가 대본 속 중요한 사물과 어떻게 상호작용하는지 명확히 그리십시오. 사물은 단순하지만 그 특징이 명확해야 합니다.
    11. 캐릭터 연출 : 스틱맨은 시대를 반영하는 의상과 헤어스타일을 연출한다.

    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 이미지 생성 AI가 그릴 수 있는 **구체적인 묘사 프롬프트**를 작성하십시오.
    
    [작성 요구사항]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **포함 요소:**
        - **텍스트 지시:** (중요) 이미지에 들어갈 텍스트를 반드시 **'{target_language}'**로 명시하십시오.
        - **안전한 묘사:** 잔인한 장면은 은유적으로 표현하여 필터링을 피하십시오.
        - **시대적 배경:** 대본의 시대(고대/중세/근대)와 장소(동양/서양)를 명확히 반영한 배경 묘사.
        - **캐릭터 연기:** 상황에 따른 캐릭터의 감정 표정과 동작(얼굴의 눈,입 필수 연출)
            - 단순한 스틱맨이라도 상황에 따른 감정 표현을 사용하십시오.
            - **얼굴 디테일:** **'눈'과 '입'의 모양을 반드시 구체적으로 묘사**하십시오. (예: 공포에 질려 덜덜 떨리는 입, 분노로 이가 갈리도록 꽉 다문 입, 폭포수처럼 쏟아지는 눈물 등)
            - **역동적 몸짓:** 정적인 자세 대신 감정을 온몸으로 표현하는 동작을 묘사하십시오. 
        - 배경 보다는 인물과 상황에 더 초점을 맞춘다.
        - 자막 같은 연출 하지 않는다. ("화면 하단 중앙에는 명조체로 **'필리핀, 1944년'**이라는 한글 텍스트가 선명하게 새겨져 있다" 이런 연출 하면 안된다) 

    [🎭 캐릭터 감정 연기 지침 (Character Acting Guide) - 중요]
    얼굴 표정이 단순한 스틱맨이므로, **몸짓과 표정(Body Language)**으로 감정을 표현하십시오.
    
    - 금지: 피(Blood), 출혈, 시체(Corpse, Dead body), 잘린 머리(Decapitation), 고문, 자살, 뼈/해골(Skeleton), 내장, 리얼한 총/칼(Weapon).
    - 금지: 나치(Nazi), 욱일기 등 정치적으로 극도로 민감한 심볼.

    [🛡️ 검열 회피를 위한 '시각적 은유(Visual Metaphors)' 가이드]
    대본 내용이 잔인하거나 폭력적일 경우, 반드시 아래의 **상징물**로 대체하여 묘사하십시오.
    
    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가적인 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """
        
    elif genre_mode == "webtoon":
        full_instruction = f"""
    [역할]
    당신은 네이버 웹툰 스타일의 **'인기 웹툰 메인 작화가'**입니다.
    독자들이 1초 만에 이해하고 클릭하고 싶게 만드는 **'트렌디하고 역동적인 웹툰 컷'**을 그려야 합니다.

    [전체 영상 주제] "{video_title}"
    [그림 스타일 가이드] {style_instruction}

    [필수 연출 지침]
    1. **작화 스타일:** 한국 웹툰(K-Webtoon) 특유의 **선명한 외곽선(Sharp Outlines)**과 **화려한 채색(Vibrant Coloring)**을 사용하십시오.
    2. **캐릭터 디자인:** **스틱맨 절대 금지.** 8등신 비율의 **'매력적인 웹툰 주인공(Anime/Manhwa Style)'**으로 묘사하십시오.
    3. **[핵심 - 배경 및 상황 강화]:**
       - 캐릭터 얼굴만 크게 그리지 말고, 캐릭터가 어디에 있는지, 주변에 무엇이 있는지 **'배경과 상황(Context & Background)'을 매우 구체적으로 묘사**하십시오.
       - 예: 방 안이라면 가구와 조명, 거리라면 건물과 행인들, 사무실이라면 책상 위의 서류까지 디테일하게 그리십시오.
    4. **[핵심 - 효과 절제]:**
       - **집중선(Speed lines)이나 과도한 이펙트는 남발하지 마십시오.** (정말 충격적인 장면에서만 가끔 사용)
       - 대신 **공간감(Depth of Field)**과 **현실적인 배경 디테일**로 상황을 설명하십시오.
    5. **카메라 앵글:** 하이 앵글, 로우 앵글, 광각 렌즈 등을 사용하되, 배경이 잘 보이도록 구도를 잡으십시오.
    6. **텍스트 처리:** {lang_guide} {lang_example}
       - 웹툰 말풍선 느낌이나 배경 오브젝트(간판, 스마트폰)에 자연스럽게 녹여내십시오.

    [임무]
    제공된 대본을 바탕으로 이미지 생성 프롬프트를 작성하십시오. (한글 출력)
    - "집중선이 배경에 깔리며..." 같은 표현은 자제하고, **"디테일한 사무실 배경을 뒤로 하고...", "비 내리는 거리 한복판에서..."** 처럼 공간 묘사를 우선하십시오.
        """

    elif genre_mode == "news":
        full_instruction = f"""
    [역할]
    당신은 뉴스 보도 및 다큐멘터리 제작을 위한 **'실사 자료화면(Stock Footage) 전문 디렉터'**입니다.
    대본 내용을 시각적으로 뒷받침하는 **'고품질 실사 사진(Hyper-Realistic Photo)'**을 기획해야 합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [필수 연출 지침]
    1. **완벽한 실사(Photorealism Only):**
       - **절대 그림, 일러스트, 3D 렌더링, 만화 느낌 금지.**
       - 실제 DSLR 카메라로 촬영한 듯한 **'뉴스 보도 사진'** 혹은 **'다큐멘터리 스틸컷'**이어야 합니다.
    2. **[매우 중요 - 분할 화면 절대 금지]:**
       - 화면을 여러 개로 나누는 **'콜라주(Collage)'나 '분할 화면(Split Screen)' 연출을 절대 금지**합니다.
       - 무조건 **'단일 화면(Single Shot)'**으로 하나의 장면에만 집중하십시오.
    3. **자료화면 연출(Stock Footage Style):**
       - 앵커가 앉아있는 스튜디오 모습이 **아닙니다.**
       - 대본의 내용을 설명하는 **현장 스케치, 인서트 컷, 사물 클로즈업, 풍경** 등을 실사로 묘사하십시오.
    4. **추상적 개념의 시각화:**
       - 예: '부동산 폭락' -> (X) 집이 무너지는 만화 (O) '매매' 스티커가 붙은 아파트 단지의 쓸쓸한 전경 또는 부동산 중개소의 텅 빈 유리창.
       - 예: '저출산' -> (X) 우는 아기 천사 (O) 텅 빈 놀이터의 그네가 흔들리는 모습.
    5. **텍스트 처리:** {lang_guide} {lang_example}
       - 텍스트는 인위적으로 띄우지 말고, 거리의 간판, 신문 헤드라인, 스마트폰 화면, 서류 내용처럼 **실제 사물에 합성**된 것처럼 자연스럽게 묘사하십시오.
    6. **조명 및 톤앤매너:**
       - 뉴스 보도에 적합한 **선명하고 사실적인 조명(Natural & Sharp Lighting)**.
       - 과도한 예술적 필터보다는 사실 전달에 집중한 톤.

    [임무]
    대본을 분석하여 AI가 생성할 수 있는 **구체적인 실사 사진 프롬프트**를 작성하십시오.
    - "Photorealistic, 8k resolution, cinematic lighting, depth of field" 등의 퀄리티 키워드 포함.
    - 인물 묘사 시 'Korean' 혹은 구체적인 인종/나이대를 명시하여 사실성 부여.
    - **한글**로만 출력하십시오.
        """

elif genre_mode == "일본 만화화":
        # [UPDATED] 현대적인 리얼리즘 드라마 + 언어 설정 완벽 적용
        full_instruction = f"""
    [역할]
    당신은 현대 사회의 단면을 예리하게 포착하는 **'고품질 현대 드라마 애니메이션 감독'**입니다.
    '시로바코(Shirobako)'나 '빙과' 처럼 **작화가 매우 사실적이고 디테일하지만, 어둡지 않고 밝고 선명한 영상미**를 추구합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [🚫 핵심 금지 사항 (Negative Constraints)]
    1. **느와르/어둠 금지:** 칙칙한 색감, 과도한 그림자, 범죄 영화 같은 무거운 분위기를 절대 금지합니다.
    2. **판타지/감성 금지:** 몽환적인 빛, 아련한 느낌, 현실에 없는 배경을 배제하십시오.
    3. **단순화 금지:** 배경을 단색으로 날리거나 캐릭터를 단순하게 그리지 마십시오.

    [필수 연출 지침 - 깔끔한 현실 묘사]
    1. **작화 스타일 (Clean Realism):**
       - **선명함(Sharpness):** 선은 깔끔하고 또렷해야 하며, 채색은 현대적이고 세련된 색감(Modern Color Palette)을 사용하십시오.
       - **조명(Lighting):** 대낮의 사무실, 밝은 카페, 맑은 거리 등 **'가시성이 좋은 자연스러운 조명'**을 기본으로 합니다.
    2. **상황 중심 연출 (Realistic Scenarios):**
       - 대본의 정보를 **'현대인의 일상 속 한 장면'**으로 치환하십시오.
       - 예: '부동산 폭락' -> 밝은 대낮, 부동산 중개소 유리창에 붙은 '급매' 전단지를 심각하게 바라보는 평범한 부부의 모습 (사실적 배경).
       - 예: '취업난' -> 깔끔한 정장을 입고 면접 대기실에 앉아 긴장하며 자신의 순서를 기다리는 청년들의 디테일한 묘사.
    3. **캐릭터 (Realistic Characters):**
       - 미형이지만 과장되지 않은, **현실적인 비율의 성인 캐릭터**를 그리십시오.
       - 복장, 헤어스타일, 소품(스마트폰, 노트북, 서류 등)을 현대적인 고증에 맞게 디테일하게 묘사하십시오.
    4. **[매우 중요] 텍스트 언어 처리 (Localization):**
       - **{lang_guide}**
       - **{lang_example}**
       - 배경의 간판, 들고 있는 서류, 스마트폰 화면, 모니터 등에 글자가 나올 경우, **반드시 위에서 지정된 언어**로만 묘사하십시오. (다른 언어 혼용 금지)

    [임무]
    대본 내용을 **'현대 사회를 배경으로 한 고화질 애니메이션 드라마의 스틸컷'**처럼 묘사하는 프롬프트를 작성하십시오.
    - **지정된 언어({target_language})가 포함된 구체적인 배경 묘사**를 반드시 포함하십시오.
    - **한글**로만 출력하십시오.
        """

    max_retries = 3
    target_models = ["gemini-3-pro-preview", "gemini-2.5-flash"]

    for attempt in range(1, max_retries + 1):
        for model_name in target_models:
            try:
                time.sleep(random.uniform(0.2, 0.5))
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_instruction + f'\n\n[대본 내용]\n"{text_chunk}"',
                    config=types.GenerateContentConfig(
                        temperature=0.75,
                        safety_settings=[
                            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
                            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
                            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
                            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
                        ]
                    )
                )

                if response.text:
                    result = response.text.strip()
                    if len(result) < 5 or result == text_chunk: continue
                    return (scene_num, result)

            except Exception as e:
                time.sleep(1)

    return (scene_num, f"주제 '{video_title}'에 어울리는 배경 일러스트 (Fallback).")

# ==========================================
# [함수] 3. 이미지 생성
# ==========================================
def generate_image(client, prompt, filename, output_dir, selected_model_name, style_instruction):
    full_path = os.path.join(output_dir, filename)
    
    final_prompt = f"{style_instruction}\n\n[장면 묘사]: {prompt}"
    max_retries = 3

    safety_settings = [
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
    ]

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=selected_model_name,
                contents=[final_prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(aspect_ratio="16:9"),
                    safety_settings=safety_settings
                )
            )
            if response.parts:
                for part in response.parts:
                    if part.inline_data:
                        img_data = part.inline_data.data
                        image = Image.open(BytesIO(img_data))
                        image.save(full_path)
                        return full_path
            time.sleep(1)
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "503" in error_msg:
                time.sleep(2 * attempt)
            else:
                time.sleep(5)
    return None

# ==========================================
# [UI] 사이드바 설정
# ==========================================
with st.sidebar:
    st.title("⚙️ 설정")

    # API Key
    api_key = ""
    try:
        if "general" in st.secrets and "google_api_key" in st.secrets["general"]:
            api_key = st.secrets["general"]["google_api_key"]
    except: pass

    if api_key:
        st.success("🔑 API Key 로드 완료")
    else:
        api_key = st.text_input("🔑 Google API Key", type="password")

    st.markdown("---")
    
    # 1. 모델 선택
    st.subheader("🖼️ 모델 선택")
    model_choice = st.radio(
        "모델 선택", 
        ("나노바나나 프로 (Gemini 3)", "나노바나나 (Gemini 2.5)"), 
        index=0,
        label_visibility="collapsed"
    )
    if "프로" in model_choice:
        SELECTED_IMAGE_MODEL = "gemini-3-pro-image-preview"
    else:
        SELECTED_IMAGE_MODEL = "gemini-2.5-flash-image"

    st.markdown("---")

    # 2. 영상 장르 선택
    st.subheader("🎨 영상 장르(Mood)")
    
    PRESET_INFO = """대사에 어울리는 2d 얼굴이 둥근 하얀색 스틱맨 연출로 설명과 이해가 잘되는 화면 자료 느낌으로 그려줘 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로
너무 어지럽지 않게, 글씨는 핵심 키워드 2~3만 나오게 한다
글씨가 너무 많지 않게 핵심만. 2D 스틱맨을 활용해 대본을 설명이 잘되게 설명하는 연출을 한다. 자막 스타일 연출은 하지 않는다.
글씨가 나올경우 핵심 키워드 중심으로만 나오게 너무 글이 많지 않도록 한다, 글자는 배경과 서물에 자연스럽게 연출, 전체 배경 연출은 2D로 디테일하게 몰입감 있게 연출해서 그려줘 (16:9)
다양한 장소와 상황 연출로 배경을 디테일하게 한다. 무조건 2D 스틱맨 연출"""
    
    PRESET_HISTORY = """역사적 사실을 기반으로 한 '2D 시네마틱 얼굴이 둥근 하얀색 스틱맨 애니메이션' 스타일.
깊이 있는 색감(Dark & Rich Tone)과 극적인 조명 사용.
캐릭터는 2D 실루엣이나 스틱맨이지만 시대에 맞는 의상과 헤어스타일을 착용.
2D 스틱맨을 활용해 대본을 설명이 잘되게 설명하는 연출을 한다. 자막 스타일 연출은 하지 않는다.
전쟁, 기근 등의 묘사는 상징적이고 은유적으로 표현. 너무 고어틱한 연출은 하지 않는다.
배경 묘사에 디테일을 살려 시대적 분위기를 강조. 무조건 얼굴이 둥근 2D 스틱맨 연출."""

    PRESET_WEBTOON = """한국 인기 웹툰 스타일의 고퀄리티 2D 일러스트레이션 (Korean Webtoon Style).
선명한 펜선과 화려한 채색. 집중선(Speed lines)은 정말 중요한 순간에만 가끔 사용.
캐릭터는 8등신 웹툰 주인공 스타일. 캐릭터 주변의 '상황'과 '배경(장소)'을 아주 구체적이고 밀도 있게 묘사.
단순 인물 컷보다는 주변 사물과 배경이 함께 보이는 구도 선호. 
전체적으로 배경 디테일이 살아있는 네이버 웹툰 썸네일 스타일. (16:9)"""

    PRESET_NEWS = """뉴스 보도용 '고화질 실사 자료화면(Photorealistic Stock Footage)'.
그림이나 만화 느낌이 전혀 없는, 실제 DSLR 카메라로 촬영한 듯한 4K 실사(Real Photo) 퀄리티.
뉴스 스튜디오가 아닌, 대본 내용을 설명하는 사실적인 '현장 스케치', '인서트 컷', '사물 클로즈업'.
인물은 실제 한국 사람(Korean)처럼, 배경은 실제 장소처럼 사실적으로 묘사.
추상적인 내용은 은유적인 실사 자료화면 느낌으로 연출. (16:9, Cinematic Lighting)
분활화면이 아니라 대본에 어울리는 내용을 하나의 화면으로 연출"""

    # [UPDATED] 일본 만화 프리셋 (디테일 강조)
    PRESET_MANGA = """[정보 전달형 고퀄리티 애니메이션]
단순한 풍경화나 감성 짤이 아님. 대본의 내용을 설명하는 '확실한 상황(Situation)'을 연출.
예: '부동산 폭락' -> 텅 빈 도시에서 무너지는 집 모형을 들고 절망하는 캐릭터.
예: '성공의 열쇠' -> 거대한 황금 열쇠를 향해 달려가는 역동적인 캐릭터.
작화는 '주술회전', '최애의 아이' 같은 최신 트렌디한 일본 애니메이션 스타일 유지.
캐릭터와 배경은 실제 현실 비율과 동일하게 정밀 묘사.
핵심 키워드 1~2개 정도는 화면에 만화적 연출로 포함 가능.
분활화면이 아니라 대본에 어울리는 내용을 하나의 화면으로 연출.(16:9)"""

    if 'style_prompt_area' not in st.session_state:
        st.session_state['style_prompt_area'] = PRESET_INFO

    def update_style_text():
        selection = st.session_state.genre_radio
        if "밝은 정보" in selection:
            st.session_state['style_prompt_area'] = PRESET_INFO
        elif "역사/다큐" in selection:
            st.session_state['style_prompt_area'] = PRESET_HISTORY
        elif "웹툰" in selection:
            st.session_state['style_prompt_area'] = PRESET_WEBTOON
        elif "일본 만화" in selection:
            st.session_state['style_prompt_area'] = PRESET_MANGA
        else:
            st.session_state['style_prompt_area'] = PRESET_NEWS

    genre_select = st.radio(
        "장르 선택", 
        ("밝은 정보/이슈 (Bright & Flat)", "역사/다큐 (Cinematic & Immersive)", "한국 웹툰 (K-Webtoon Style)", "일본 만화 (Japanese Manga/Anime)", "뉴스/실사 자료화면 (Realistic Footage)"), 
        index=0,
        key="genre_radio",
        on_change=update_style_text,
        label_visibility="collapsed"
    )

    if "밝은 정보" in genre_select:
        SELECTED_GENRE_MODE = "info"
    elif "역사/다큐" in genre_select:
        SELECTED_GENRE_MODE = "history"
    elif "웹툰" in genre_select:
        SELECTED_GENRE_MODE = "webtoon"
    elif "일본 만화" in genre_select:
        SELECTED_GENRE_MODE = "manga"
    else:
        SELECTED_GENRE_MODE = "news"

    st.markdown("---")

    # 3. 이미지 텍스트 언어 선택
    st.subheader("🌐 이미지 텍스트 언어")
    target_language = st.selectbox(
        "이미지 텍스트 언어",
        ("Korean", "English", "Japanese"),
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.subheader("🖌️ 그림체 지침 (수정 가능)")
    style_instruction = st.text_area(
        "스타일 지침", 
        key="style_prompt_area",
        height=250,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.subheader("⏱️ 설정")
    chunk_duration = st.slider("장면 시간(초):", 5, 60, 30, 5)
    chars_limit = chunk_duration * 8
    max_workers = st.slider("작업 속도:", 1, 10, 5)

# ==========================================
# [UI] 메인 화면
# ==========================================
st.title("🎬 AI 이미지 생성기 (Pro)")
st.caption(f"다크모드 & 빅 텍스트 | 🎨 Model: {SELECTED_IMAGE_MODEL} | 🎭 Mode: {genre_select}")

# 세션 초기화
if 'generated_results' not in st.session_state:
    st.session_state['generated_results'] = []
if 'video_title' not in st.session_state:
    st.session_state['video_title'] = ""

st.write("")

# 1. 제목 입력
col_title_input, col_space = st.columns([3, 1])
with col_title_input:
    st.text_input(
        "📌 영상 제목/주제 (선택사항)",
        key="video_title",
        placeholder="예: 부자들의 3가지 습관 (전체 분위기 결정)",
    )

st.write("")
script_input = st.text_area("📜 대본 입력 (여기에 붙여넣기)", height=350, placeholder="안녕하세요. 오늘은...")

def clear_generated_results():
    st.session_state['generated_results'] = []
    gc.collect()

st.write("")
start_btn = st.button("🚀 이미지 생성 시작하기", type="primary", use_container_width=True, on_click=clear_generated_results)

if start_btn:
    if not api_key:
        st.error("⚠️ Google API Key 필요")
    elif not script_input:
        st.warning("⚠️ 대본을 입력해주세요.")
    else:
        user_id = st.session_state['user_id']
        USER_DIR = os.path.join(BASE_PATH, user_id, "output_images")

        st.session_state['generated_results'] = []
        if os.path.exists(USER_DIR):
            try: shutil.rmtree(USER_DIR)
            except: pass
        os.makedirs(USER_DIR, exist_ok=True)

        client = genai.Client(api_key=api_key)
        status_box = st.status("작업 진행 중...", expanded=True)
        progress_bar = st.progress(0)

        # 1. 대본 분할
        status_box.write(f"✂️ 대본 분할 중...")
        chunks = split_script_by_time(script_input, chars_per_chunk=chars_limit)
        total_scenes = len(chunks)
        status_box.write(f"✅ {total_scenes}개 장면으로 분할 완료.")
        
        current_video_title = st.session_state.get('video_title', "").strip()
        if not current_video_title:
            current_video_title = "전반적인 대본 분위기에 어울리는 배경"

        # 2. 프롬프트 생성 (병렬)
        status_box.write(f"📝 프롬프트 작성 중... (Mode: {SELECTED_GENRE_MODE}, Lang: {target_language})")
        prompts = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i, chunk in enumerate(chunks):
                futures.append(executor.submit(
                    generate_prompt,
                    api_key, i, chunk, 
                    style_instruction,
                    current_video_title,
                    SELECTED_GENRE_MODE, # 장르 전달
                    target_language      # 언어 전달
                ))
            
            for i, future in enumerate(as_completed(futures)):
                prompts.append(future.result())
                progress_bar.progress((i + 1) / (total_scenes * 2))

        prompts.sort(key=lambda x: x[0])

        # 3. 이미지 생성 (병렬)
        status_box.write(f"🎨 이미지 생성 중 ({SELECTED_IMAGE_MODEL})...")
        results = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_meta = {}
            for s_num, prompt_text in prompts:
                idx = s_num - 1
                orig_text = chunks[idx]
                fname = make_filename(s_num, orig_text)
                time.sleep(0.05)
                
                future = executor.submit(
                    generate_image,
                    client, prompt_text, fname, USER_DIR,
                    SELECTED_IMAGE_MODEL, 
                    style_instruction
                )
                future_to_meta[future] = (s_num, fname, orig_text, prompt_text)

            completed_cnt = 0
            for future in as_completed(future_to_meta):
                s_num, fname, orig_text, p_text = future_to_meta[future]
                path = future.result()
                if path:
                    results.append({
                        "scene": s_num, "path": path, "filename": fname, 
                        "script": orig_text, "prompt": p_text
                    })
                completed_cnt += 1
                progress_bar.progress(0.5 + (completed_cnt / total_scenes * 0.5))

        results.sort(key=lambda x: x['scene'])
        st.session_state['generated_results'] = results
        status_box.update(label="✅ 생성 완료!", state="complete", expanded=False)

# ==========================================
# [결과 화면]
# ==========================================
if st.session_state['generated_results']:
    user_id = st.session_state['user_id']
    CURRENT_USER_DIR = os.path.join(BASE_PATH, user_id, "output_images")

    st.divider()
    st.markdown(f"## 📸 결과물 ({len(st.session_state['generated_results'])}장)")
    
    zip_data = create_zip_buffer(CURRENT_USER_DIR)
    st.download_button("📦 전체 이미지 ZIP 다운로드", data=zip_data, file_name="all_images.zip", mime="application/zip", use_container_width=True)
    st.markdown("---")

    for index, item in enumerate(st.session_state['generated_results']):
        with st.container(border=True):
            cols = st.columns([1, 2])
            
            # [오른쪽: 정보 및 수정]
            with cols[1]:
                st.markdown(f"### Scene {item['scene']:02d}")
                st.markdown(f"**대본:**\n\n{item['script']}")
                
                with st.expander("📝 프롬프트 수정 & 확인", expanded=False):
                    prompt_key = f"prompt_edit_{index}"
                    edited_prompt = st.text_area(
                        "프롬프트 내용을 수정하고 왼쪽의 [이미지 다시 생성] 버튼을 누르세요.",
                        value=item['prompt'],
                        height=150,
                        key=prompt_key
                    )

            # [왼쪽: 이미지 및 버튼]
            with cols[0]:
                try: st.image(item['path'], use_container_width=True)
                except: st.error("이미지 없음")

                if st.button(f"🔄 이미지 다시 생성", key=f"regen_img_{index}", use_container_width=True):
                    if not api_key: st.error("API Key 필요")
                    else:
                        current_prompt_text = st.session_state.get(prompt_key, item['prompt'])

                        with st.spinner(f"Scene {item['scene']} 재생성 중..."):
                            client = genai.Client(api_key=api_key)
                            
                            new_path = generate_image(
                                client, 
                                current_prompt_text, 
                                item['filename'],
                                CURRENT_USER_DIR, 
                                SELECTED_IMAGE_MODEL, 
                                style_instruction
                            )
                            
                            if new_path:
                                st.session_state['generated_results'][index]['path'] = new_path
                                st.session_state['generated_results'][index]['prompt'] = current_prompt_text
                                st.rerun()
                
                try:
                    with open(item['path'], "rb") as file:
                        st.download_button("⬇️ 이미지 저장", data=file, file_name=item['filename'], mime="image/png", key=f"btn_down_{item['scene']}")

                except: pass






