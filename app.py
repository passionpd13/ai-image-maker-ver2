import streamlit as st
import requests
import random
import json
import time
import os
import re
import shutil
import zipfile
import uuid  # [수정] 고유 세션 ID 생성을 위한 라이브러리 추가
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from google import genai
from google.genai import types

# ==========================================
# [설정] 페이지 기본 설정
# ==========================================
st.set_page_config(
    page_title="열정피디 AI 씬 생성기 (Image Only)", 
    layout="wide", 
    page_icon="🎨",
    initial_sidebar_state="expanded"
)

# ==========================================
# [디자인] 다크모드 & CSS 스타일 (원본 100% 유지)
# ==========================================
st.markdown("""
    <style>
    /* [1] 앱 전체 강제 다크모드 */
    .stApp {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
        font-family: 'Pretendard', sans-serif;
    }

    /* [2] 사이드바 텍스트 하얗게 */
    section[data-testid="stSidebar"] {
        background-color: #12141C !important;
        border-right: 1px solid #2C2F38;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    /* [3] Expander (프롬프트 확인) 가독성 완벽 해결 */
    [data-testid="stExpander"] {
        background-color: #1F2128 !important;
        border: 1px solid #4A4A4A !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }
      
    [data-testid="stExpander"] summary {
        color: #FFFFFF !important;
    }
    [data-testid="stExpander"] summary:hover {
        color: #FF4B2B !important; /* 호버 시 주황색 포인트 */
    }
    [data-testid="stExpander"] summary svg {
        fill: #FFFFFF !important;
    }

    /* [중요] Expander 내부 콘텐츠 영역 */
    [data-testid="stExpander"] details > div {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
    }
      
    /* 내부의 모든 텍스트 요소 강제 흰색 */
    [data-testid="stExpander"] p, 
    [data-testid="stExpander"] span, 
    [data-testid="stExpander"] div,
    [data-testid="stExpander"] code {
        color: #FFFFFF !important;
        background-color: transparent !important;
    }

    /* [4] 파일 업로더 가독성 해결 */
    [data-testid="stFileUploader"] {
        background-color: #262730 !important;
        border-radius: 10px;
        padding: 15px;
    }
    [data-testid="stFileUploader"] section {
        background-color: #262730 !important; 
    }
    [data-testid="stFileUploader"] div, 
    [data-testid="stFileUploader"] span, 
    [data-testid="stFileUploader"] small {
        color: #FFFFFF !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #0E1117 !important;
        color: #FFFFFF !important;
        border: 1px solid #555 !important;
    }

    /* [5] 모든 버튼 스타일 */
    .stButton > button {
        background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(255, 75, 43, 0.4);
    }
    .stButton > button * {
        color: #FFFFFF !important;
    }

    /* [6] 입력창 스타일 */
    .stTextInput input, .stTextArea textarea {
        background-color: #262730 !important; 
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid #4A4A4A !important;
        caret-color: #FF4B2B !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #B0B0B0 !important;
        -webkit-text-fill-color: #B0B0B0 !important;
    }

    /* [7] 드롭다운(Selectbox) */
    div[data-baseweb="select"] > div {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border-color: #4A4A4A !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #262730 !important;
    }
    div[data-baseweb="option"], li[role="option"] {
        color: #FFFFFF !important;
        background-color: #262730 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background-color: #FF4B2B !important;
        color: #FFFFFF !important;
    }

    /* [8] 다운로드 버튼 */
    [data-testid="stDownloadButton"] button {
        background-color: #2C2F38 !important;
        border: 1px solid #555 !important;
    }
    [data-testid="stDownloadButton"] button * {
        color: #FFFFFF !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        border-color: #FF4B2B !important;
    }
    [data-testid="stDownloadButton"] button:hover * {
        color: #FF4B2B !important;
    }

    /* [9] 기타 텍스트 */
    h1, h2, h3, h4, p, label, li {
        color: #FFFFFF !important;
    }
    .stCaption {
        color: #AAAAAA !important;
    }
    header[data-testid="stHeader"] {
        background-color: #0E1117 !important;
    }

    /* [10] st.status (작업 진행 상태창) */
    [data-testid="stStatusWidget"] {
        background-color: #1F2128 !important;
        border: 1px solid #4A4A4A !important;
    }
    [data-testid="stStatusWidget"] > div {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
    }
    [data-testid="stStatusWidget"] header {
        background-color: #1F2128 !important;
    }
    [data-testid="stStatusWidget"] svg {
        fill: #FFFFFF !important;
    }
    [data-testid="stStatusWidget"] p, 
    [data-testid="stStatusWidget"] span,
    [data-testid="stStatusWidget"] summary {
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# [중요 수정] 멀티 유저 세션 분리 로직
# ==========================================
# 각 사용자(브라우저 탭)마다 고유한 세션 ID를 생성하여 폴더가 겹치지 않게 합니다.
if 'user_session_id' not in st.session_state:
    st.session_state['user_session_id'] = str(uuid.uuid4())

# 파일 저장 경로 설정 (사용자별 고유 경로 사용)
BASE_PATH = "./web_result_files"
# 예: ./web_result_files/a1b2-c3d4.../output_images 형태로 저장됨
IMAGE_OUTPUT_DIR = os.path.join(BASE_PATH, st.session_state['user_session_id'], "output_images")

# 텍스트 모델 설정
GEMINI_TEXT_MODEL_NAME = "gemini-2.5-pro" 

# ==========================================
# [함수] 1. 유틸리티 함수
# ==========================================
def init_folders():
    # [수정] 전체 폴더 삭제가 아니라, 현재 유저의 폴더만 관리
    if not os.path.exists(IMAGE_OUTPUT_DIR):
        os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

def split_script_by_time(script, chars_per_chunk=100):
    # 일본어 구두점 및 줄바꿈(\n)도 확실하게 분리하도록 개선
    temp_script = script.replace(".", ".|").replace("?", "?|").replace("!", "!|") \
                        .replace("。", "。|").replace("？", "？|").replace("！", "！|") \
                        .replace("\n", "\n|")

    temp_sentences = temp_script.split("|")
                              
    chunks = []
    current_chunk = ""
    
    for sentence in temp_sentences:
        sentence = sentence.strip()
        if not sentence: continue
        
        if len(current_chunk) + len(sentence) < chars_per_chunk:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk.strip(): 
                chunks.append(current_chunk.strip())
            
            current_chunk = sentence
            
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

def make_filename(scene_num, text_chunk):
    clean_line = text_chunk.replace("\n", " ").strip()
    clean_line = re.sub(r'[\\/:*?"<>|]', "", clean_line)
    
    if not clean_line:
        return f"S{scene_num:03d}_Scene.png"
    
    words = clean_line.split()
    
    if len(words) <= 1 or any(ord(c) > 12000 for c in clean_line[:10]): 
        if len(clean_line) > 16:
            summary = f"{clean_line[:10]}...{clean_line[-10:]}"
        else:
            summary = clean_line
    else:
        if len(words) <= 6:
            summary = " ".join(words)
        else:
            start_part = " ".join(words[:3])
            end_part = " ".join(words[-3:])
            summary = f"{start_part}...{end_part}"
            
            if len(summary) > 50:
                summary = summary[:50]
    
    filename = f"S{scene_num:03d}_{summary}.png"
    return filename

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
# [함수] 2. 프롬프트 생성 (오류 수정 및 재시도 로직 강화)
# ==========================================
def generate_prompt(api_key, index, text_chunk, style_instruction, video_title, genre_mode="info", target_language="Korean", character_desc="", target_layout="16:9 와이드 비율"):
    scene_num = index + 1
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_TEXT_MODEL_NAME}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}

    # [언어 설정 로직]
    if target_language == "Korean":
        lang_guide = "화면 속 글씨는 **무조건 '한글(Korean)'로 표기**하십시오. (다른 언어 절대 금지)"
        lang_example = "(예: '뉴욕', '도쿄')"
    elif target_language == "English":
        lang_guide = "화면 속 글씨는 **무조건 '영어(English)'로 표기**하십시오."
        lang_example = "(예: 'Seoul', 'Dokdo')"
    elif target_language == "Japanese":
        lang_guide = "화면 속 글씨는 **무조건 '일본어(Japanese)'로 표기**하십시오."
        lang_example = "(예: 'ソウル', 'ニューヨーク')"
    else:
        lang_guide = f"화면 속 글씨는 **무조건 '{target_language}'로 표기**하십시오."
        lang_example = ""

    # ------------------------------------------------------
    # [NEW] 캐릭터 일관성 유지 지침 블록 생성
    # ------------------------------------------------------
    character_consistency_block = ""
    if character_desc and "Error" not in character_desc:
        character_consistency_block = f"""
    [⭐⭐⭐ 비주얼 일관성 유지 핵심 지침 (최우선 순위) ⭐⭐⭐]
    모든 장면에 등장하는 주인공 캐릭터는 반드시 아래의 상세 묘사와 시각적으로 일치해야 합니다.
    절대로 이 캐릭터의 핵심적인 외형 특징을 바꾸지 마십시오.

    **[Reference Character Visual Blueprint]:**
    {character_desc}
    ---------------------------------------------------------
        """

    # ------------------------------------------------------
    # [수정됨] 9:16 강력 보정 로직 (Vertical Layout Injection)
    # ------------------------------------------------------
    vertical_force_prompt = ""
    if "9:16" in target_layout:
        vertical_force_prompt = """
    [❗❗ 9:16 세로 화면 필수 지침 (Vertical Mode) ❗❗]
    1. **구도(Composition):** 가로로 넓은 풍경(Landscape)을 절대 그리지 마십시오.
    2. **배치(Placement):** 피사체는 화면 중앙에 수직으로 배치되어야 합니다. (위아래로 길게)
    3. **치타/동물 예시:** 동물이 달리는 장면이라면, 옆모습(Side view) 대신 **정면에서 달려오는 모습(Front view)**을 구도를 사용하여 세로 화면을 채우십시오.
        """

    # 공통 헤더 (모든 모드에 주입)
    common_header = f"""
    {character_consistency_block}
    [화면 구도 지침]
    {target_layout}
    {vertical_force_prompt}
    """

    # ---------------------------------------------------------
    # [모드 1] 밝은 정보/이슈
    # ---------------------------------------------------------
    if genre_mode == "info":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 복잡한 상황을 아주 쉽고 직관적인 그림으로 표현하는 '비주얼 커뮤니케이션 전문가'이자 '교육용 일러스트레이터'입니다.

    [전체 영상 주제]
    "{video_title}"

    [그림 스타일 가이드 - 절대 준수]
    {style_instruction}
      
    [필수 연출 지침]
    1. **조명(Lighting):** 무조건 **'몰입감있는 조명(High Key Lighting)'**을 사용하십시오.
    2. **색감(Colors):** 선명한 색상을 사용하여 시인성을 높이십시오. (칙칙하거나 회색조 톤 금지)
    3. **구성(Composition):** 시청자가 상황을 한눈에 이해할 수 있도록 피사체를 화면 중앙에 명확하게 배치하십시오.
    4. **분위기(Mood):** 교육적이지만 사실적, 중립적이며, 몰입감있는 분위기여야 합니다. **(절대 우울하거나, 무섭거나, 기괴한 느낌 금지)**
    5. 분활화면으로 연출하지 말고 하나의 화면으로 연출한다.
    6. **[텍스트 언어]:** {lang_guide} {lang_example}
    - **[절대 금지]:** 화면의 네 모서리(Corners)나 가장자리(Edges)에 글자를 배치하지 마십시오. 글자는 반드시 중앙 피사체 주변에만 연출하십시오.
    7. 캐릭터의 감정도 느껴진다.
    8. 특정 국가에 대한 내용일시 배경에 국가 분위기가 연출 잘되게 한다.
    9. 배경 현실감(Background Realism): 배경은 단순한 평면이 아닌, **깊이감(Depth)**과 **질감(Texture)**이 살아있는 입체적인 공간으로 연출하십시오. 추상적이거나 흐릿한 배경 대신, 실제 장소에 있는 듯한 **구체적인 환경 디테일(건축 양식, 자연물, 소품 배치, 거리, 공간간 등)을 선명하게 묘사하여 2d이지만 현장감을 극대화하십시오.


    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 이미지 생성 AI가 그릴 수 있는 **구체적인 묘사 프롬프트**를 작성하십시오.
      
    [작성 요구사항]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **세로 모드 시:** 캐릭터나 사물이 작아 보이지 않게 줌인(Zoom-in)하여 묘사하십시오.
    - **포함 요소:**
        - **캐릭터 행동:** 대본의 상황을 연기하는 캐릭터의 구체적인 동작.
        - **배경:** 상황을 설명하는 소품이나 장소를 몰입감 있고 깊이감 있게 2d로 구성. 
        - **시각적 은유:** 추상적인 내용일 경우, 이를 설명할 수 있는 시각적 아이디어 (예: 돈이 날아가는 모습, 그래프가 하락하는 모습 등).
          한글 뒤에 (영어)를 넣어서 프롬프트에 쓰지 않는다. ex) 색감(Colors) x ,구성(Composition) x

      
    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가적인 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

    # ---------------------------------------------------------
    # [모드 NEW] 스틱맨 사실적 연출 (Realistic Stickman Drama)
    # ---------------------------------------------------------
    elif genre_mode == "realistic_stickman":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **'넷플릭스 2D 애니메이션 감독'**입니다. 
    **반드시 '2D 그림(Digital Art)' 스타일**이어야 하며, **실사(Photorealism)나 3D 렌더링 느낌이 나면 절대 안 됩니다.**
    단순한 얼굴이 둥근 스틱맨들을 주인공으로 사용하여, 배경과 조명만 영화처럼 분위기 있게 연출합니다.
      
    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [🚫 핵심 금지 사항 - 절대 어기지 마시오]
    - **실사 사진(Real Photo), 3D 렌더링(Unreal Engine), 사람 피부 질감(Skin texture) 절대 금지.**
    - 사람의 코, 입, 귀, 손톱 등을 리얼하게 묘사하지 마시오.
    - 무조건 **'그림(Illustration/Drawing/Manhwa)'** 느낌이 나야 합니다.

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **캐릭터(Character):** - **얼굴이 둥근 하얀색 스틱맨(Round-headed white stickman)**을 사용하십시오.
        - 하지만 선은 굵고 부드러우며, **그림자(Shading)**가 들어가 입체감이 느껴져야 합니다.
        - **의상:** 대본 상황에 맞는 현실적인 의상(정장, 군복, 잠옷, 작업복 등)을 스틱맨 위에 입혀 '캐릭터성'을 부여하십시오.
        - 얼굴이 크게 잘 보이게 연출. 장면도 잘 드러나게.
          
    2. **배경(Background) - 가장 중요:**
        - 단순한 그라데이션이나 단색 배경을 **절대 금지**합니다.
        - **고해상도 컨셉 아트(High-quality Concept Art)** 수준으로 배경을 그리십시오.
        - 예: 사무실이라면 책상의 서류 더미, 창밖의 풍경, 커피잔의 김, 벽의 질감까지 묘사해야 합니다.
          
    3. **조명(Lighting):**
        - 2D지만 **입체적인 조명(Volumetric Lighting)**과 그림자를 사용하여 깊이감을 만드십시오.
        - 상황에 따라 따뜻한 햇살, 차가운 네온사, 어두운 방의 스탠드 조명 등을 명확히 구분하십시오.
          
    4. **연기(Acting):**
        - 인포그래픽처럼 정보를 나열하지 말고, **캐릭터가 행동(Action)하는 장면**을 포착하십시오.
        - 감정 표현: 얼굴 표정은 단순하게 가되, **어깨의 처짐, 주먹 쥔 손, 다급한 달리기, 무릎 꿇기 등 '몸짓(Body Language)'**으로 감정을 전달하십시오.

    5. **언어(Text):** {lang_guide} {lang_example} (자막 연출보다는 배경 속 간판, 서류, 화면 등 자연스럽게 텍스트 위주로)
    6. **구도:** 분할 화면(Split Screen) 금지. **{target_layout}** 꽉 찬 구도 사용.

    [임무]
    제공된 대본 조각(Script Segment)을 읽고, 그 상황을 가장 잘 보여주는 **한 장면의 영화 스틸컷** 같은 프롬프트를 작성하십시오.
      
    [작성 팁]
    - "A cinematic 2D shot of a round-headed stickman..." 으로 시작하는 느낌으로 작성.
    - 대본이 추상적(예: 경제 위기)이라면, 스틱맨이 텅 빈 지갑을 보며 좌절하는 구체적인 상황으로 치환하여 묘사하십시오.
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - 자막 같은 연출 하지 않는다. ("화면 하단 중앙에는 명조체로 **'필리핀, 1944년'**이라는 한글 텍스트가 선명하게 새겨져 있다" 이런 연출 하면 안된다) 

    [9:16 세로 모드 팁]
    - 스틱맨이 화면의 50% 이상을 차지하도록 가까이서 잡으십시오.
    - 배경 위주가 아니라 **캐릭터의 연기 위주**로 프레임을 구성하십시오.

    [출력 형식]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

    # ---------------------------------------------------------
    # [모드 2] 역사/다큐 (수정됨: else -> elif)
    # ---------------------------------------------------------
    elif genre_mode == "history":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **세계사의 결정적인 순간들(한국사, 서양사, 동양사 등)**을 한국 시청자에게 전달하는 '시대극 애니메이션 감독'입니다.
    역사적 비극을 다루지만, 절대로 잔인하거나 혐오스럽거나 고어틱하게 묘사를 하지 않습니다.

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
    - 9:16 비율일 경우, 역사적 인물(스틱맨)의 **상반신 위주**로 묘사하여 표정(눈매)이나 손짓이 잘 보이게 하십시오.
    - **포함 요소:**
        - **텍스트 지시:** (중요) 이미지에 들어갈 텍스트를 반드시 **'{target_language}'**로 명시하십시오.
            - 텍스트는 그래픽 연출이 아니라 화면의 사물에 자연스럽게 연출되게 한다.
        - **안전한 묘사:** 잔인한 장면은 은유적으로 표현하여 필터링을 피하십시오.
        - **시대적 배경:** 대본의 시대(고대/중세/근대)와 장소(동양/서양)를 명확히 반영한 배경 묘사.
        - **[수정됨] 절제된 캐릭터 연기 묘사:**
            - 스틱맨의 얼굴은 **단순한 선으로 표현된 슬픈 눈매, 굳게 다문 입매** 정도로 절제하여 묘사하십시오. (기괴한 표정 묘사 금지)
            - 스틱맨의 시대적 의상과 헤어스타일을 연출한다.
            - **감정은 몸짓으로 표현하십시오.** (예: 고개를 깊이 숙인 모습, 얼굴을 감싸 쥔 손, 힘없이 축 늘어진 어깨, 무릎 꿇고 기도하는 자세 등 정적인 동작 위주)
        - 배경 보다는 대본에 어울리는 인물들과 상황 연출에 더 초점을 맞춘다.
        - 자막 같은 연출 하지 않는다. ("화면 하단 중앙에는 명조체로 **'필리핀, 1944년'**이라는 한글 텍스트가 선명하게 새겨져 있다" 이런 연출 하면 안된다) 
      
    [🎭 캐릭터 감정 연기 지침 (Character Acting Guide) - 중요]
    **얼굴 표정이 단순한 스틱맨이므로, '몸짓(Body Language)'으로 감정을 표현하는 데 집중하십시오.**
      
    - 금지: 피(Blood), 출혈, 시체(Corpse, Dead body), 잘린 머리(Decapitation), 고문, 자살, 뼈/해골(Skeleton), 내장, 리얼한 총/칼(Weapon).
    - **추가 금지:** 과도하게 일그러진 얼굴 표정, 공포에 질려 비명 지르는 입 모양 등 자극적인 얼굴 묘사.
    - 금지: 나치(Nazi), 욱일기 등 정치적으로 극도로 민감한 심볼.
      
    [🛡️ 검열 회피를 위한 '시각적 은유(Visual Metaphors)' 가이드]
    대본 내용이 비극적이거나 폭력적일 경우, 반드시 아래의 **부드러운 상징물**로 대체하여 묘사하십시오.
      
    [출력 형식]
    - **무조건 한국어**로만 작성하십시오.
    - 부가적인 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
    - (지문) 같은 부연설명 연출 지시어는 제외한다.

    - 프롬프트에 '얼굴이 둥근 2d 스틱맨' 무조건 들어간다.
        """

    # ---------------------------------------------------------
    # [모드 3] 3D 다큐멘터리 (현대/미스터리)
    # ---------------------------------------------------------
    elif genre_mode == "3d_docu":
        # 9:16일 경우 인물 확대 지침 정의
        vertical_zoom_guide = ""
        if "9:16" in target_layout:
            vertical_zoom_guide = """
    5. **[9:16 세로 모드 필수 지침 - 인물 확대]:**
        - 스마트폰 화면(세로) 특성상 인물이 멀리 있으면 시인성이 떨어집니다.
        - **카메라를 피사체(마네킹) 가까이(Close-up, Medium Shot) 배치하여, 머리와 상반신이 화면의 50% 이상을 차지하도록 꽉 차게 연출하십시오.**
        - 다양한 장소 표현을 디테일 하게, 그리고 사물 묘사도 디테일하게.
        - 전신 샷(Full Shot)과 클로즈업 위주로 묘사하십시오.
            """

        full_instruction = f"""
    {common_header}
    [역할]
    당신은 'Unreal Engine 5'를 사용하는 3D 시네마틱 아티스트입니다.
    현대 사회의 이슈나 미스터리한 현상을 고퀄리티 3D 그래픽으로 시각화합니다.

    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **화풍 (Art Style):** "A realistic 3D game cinematic screenshot", "Unreal Engine 5 render style", "8k resolution", "Highly detailed texture".
    2. **캐릭터 디자인 (Character Design):** - 등장인물의 머리는 반드시 **"매끈하고 하얀, 이목구비가 없는 마네킹 머리 (Smooth white featureless mannequin head)"**여야 합니다.
        - **얼굴 묘사 금지:** 눈, 코, 입이 절대 없어야 합니다 (Blank face, No eyes/nose/mouth).
        - **의상:** 하지만 몸에는 **현실적인 의상(정장, 가디건, 청바지, 유니폼 등)**을 입혀서 기묘하고 현대적인 느낌을 줍니다.
    3. **조명 및 분위기 (Lighting & Mood):** - "Cinematic lighting", "Dim lighting", "Volumetric fog".
        - 다소 어둡고, 밝기도 하며, 미스터리하며, 진지한 분위기를 연출하십시오.
    4. **언어 (Text):** {lang_guide} {lang_example} (가능한 텍스트 묘사는 줄이고 상황 묘사에 집중)
    {vertical_zoom_guide}

    [9:16 세로 모드 필수 지침]
    - 마네킹 캐릭터를 **'포트레이트 샷(Portrait Shot)'**으로 잡으십시오.
    - 전신보다는 **상반신 클로즈업**이 훨씬 효과적입니다.

    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 위 스타일이 적용된 이미지 생성 프롬프트를 작성하십시오.
      
    [작성 팁]
    - 프롬프트 시작 부분에 반드시 **"언리얼 엔진 5 스타일, Realistic 3D game screenshot, Smooth white featureless mannequin head character"** 키워드가 포함되도록 문장을 구성하십시오.
    - 대본의 상황(좌절, 성공, 회의, 폭락 등)을 마네킹 캐릭터가 연기하도록 묘사하십시오.
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.

    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오. (단, Unreal Engine 5 같은 핵심 영단어는 혼용 가능)
    - 부가 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
    - (지문) 같은 부연설명 연출 지시어는 제외한다.
        """
      
    # ---------------------------------------------------------
    # [모드 4] 과학/엔지니어링 (Clean Technical + Characters) - [NEW! 재수정됨]
    # ---------------------------------------------------------
    elif genre_mode == "scifi":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 'Fern', 'AiTelly', 'Blackfiles' 채널 스타일의 **깔끔하고 명확한 '3D 테크니컬 애니메이터'**입니다.
    복잡한 기계나 과학 원리를 설명하되, **엔지니어/과학자 캐릭터의 행동**을 통해 시청자의 이해를 돕습니다. (어둡고 과한 시네마틱 X, 밝고 명확한 교육용 O)

    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **화풍 (Art Style):** "3D Technical Animation", "Blender Cycles Render", "Clean rendering", "High detail".
    2. **분위기 및 조명 (Atmosphere & Lighting):**
        - **"Clean Studio Lighting", "Bright", "Educational"**.
        - 그림자가 너무 짙거나 어두워서는 안 됩니다. 모든 부품과 인물이 명확하게 보여야 합니다.
    3. **피사체 (Subject) - 기계와 인물의 조화:**
        - **기계/구조물:** 단면도(Cutaway), 투시도(X-ray view), 분해도(Exploded view)를 적극 활용하여 내부 작동 원리를 보여주십시오.
        - **[중요] 인물(Characters):** 대본 내용에 맞춰 엔지니어, 과학자, 작업자를 3d 게임 캐릭터 처럼 등장시키십시오.
            - **복장:** 안전모, 실험 가운, 작업복 등 전문적인 복장.
            - **행동:** 단순히 서 있는 것이 아니라, **기계를 조작하거나, 특정 부위를 가리키며 설명하거나, 단면을 관찰하는 등 '기능적인 행동'**을 취해야 합니다.
    4. **카메라 (Camera):** "Clear view", "Isometric view"(선택적), "Slight zoom"(디테일 강조). 과도한 아웃포커싱(심도)은 자제하고 전체적으로 쨍하게 보여주십시오.
    5. **언어 (Text):** {lang_guide} {lang_example} (화살표와 함께 부품 명칭을 지시할 때만 최소한으로 사용)

    [9:16 세로 모드 지침]
    - 기계 전체를 보여주려 하지 말고, **작동하는 핵심 부품을 확대(Zoom-in)**하여 세로 화면에 꽉 차게 보여주십시오.
    - 위아래 공간을 활용하여 부품이 분해되는 모습(Exploded view)을 수직으로 배치하십시오.

    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 마치 공학 교육 영상의 한 장면 같은 3D 프롬프트를 작성하십시오.
      
    [작성 팁]
    - 프롬프트 시작 부분에 반드시 **"3D technical animation, Blender Cycles render, Clean studio lighting, Cutaway view"** 키워드를 포함하십시오.
    - **인물 등장 시 행동 묘사 예시:** "안전모를 쓴 엔지니어가 거대한 터빈의 단면을 손으로 가리키고 있다", "과학자가 실험 장비를 조작하며 데이터를 확인하는 모습".
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.

    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오. (단, Cutaway, X-ray view 같은 핵심 영단어는 혼용 가능)
    - 부가 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

    # ---------------------------------------------------------
    # [모드 5] History/Satire Stickman (History Matters Style) - [수정됨: 담백함 + 공간 연출의 완급조절]
    # ---------------------------------------------------------
    elif genre_mode == "paint_explainer":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 'History Matters' 또는 'OverSimplified' 스타일의 **'세련된 미니멀리즘 애니메이션 감독'**입니다.
    기본적으로는 화면을 비우는 것을 좋아하지만, **상황에 따라 '공간감'을 연출하여 영상의 리듬감(Variety)**을 살려야 합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [핵심 비주얼 전략: '선택과 집중' + '완급 조절']
    대본을 보고 아래 두 가지 연출 중 하나를 선택하여 그리십시오. (무조건 섞여 있어야 합니다.)

    **옵션 A. [극강의 심플함 (Focus on Subject)]: (비중 60%)**
    - 배경을 **완전한 단색(Solid Color)**으로 처리하고, 오직 **'인물(표정 연기)'** 또는 **'사물(아이콘)'** 하나만 큼직하게 그립니다.
    - 예: 스틱맨이 절규하는 모습만 클로즈업, 혹은 돈다발만 화면 중앙에 배치.
    -배경은 기본은 하얀색이지만 상황에 따라 다른색으로 표현.

    **옵션 B. [미니멀한 공간 연출 (Minimal Context)]: (비중 40%)**
    - 대본에서 '장소'가 중요할 때는 **단순화된 배경**을 그립니다.
    -배경은 기본은 하얀색이지만 상황에 따라 다른색으로 표현.
    - **인물 + 실내:** 인물이 서 있는데 뒤에 **'창문 하나', '책상 하나', '감옥 창살'** 등을 그려 여기가 어디인지 암시하십시오. (벽지 무늬 등 복잡한 디테일은 생략)
    - **장소 중심:** 건물을 그릴 때는 주변 풍경을 다 그리지 말고, **'건물(하나 또는 두개) 와 바닥(지평선)'** 정도만 깔끔하게 그리십시오.

    [공통 작화 스타일 가이드]
    1. **[굵은 선 & 플랫 컬러]:**
        - 모든 요소에 **'매우 굵은 검은색 외곽선(Thick Black Outlines)'** 필수.
        - 명암/그림자 없는 **'완전한 플랫 컬러'**. 깔끔한 벡터 일러스트 느낌.

    2. **[복잡함 금지 (No Clutter)]:**
        - 배경을 그리더라도 **'종합 선물 세트'**처럼 사람, 건물, 지도, 비행기를 한 화면에 다 넣지 마십시오.
        - 배경은 인물을 설명하기 위한 **거들 뿐**이어야 합니다.

    3. **[텍스트 - 손글씨]:**
        - 마카펜으로 쓴 듯한 **'투박한 굵은 손글씨'**.
        - **[언어 엄수]:** {lang_guide}
            - **(매우 중요: 지정된 언어({lang_guide})가 아닌 다른 언어가 섞여 나오면 절대 안 됩니다. 무조건 위 언어({lang_guide})로만 표기하십시오.)**
        - 텍스트는 핵심 키워드 라벨링 용도로만 정말 최소한으로 사용.
        - **[절대 금지]:** 화면의 네 모서리(Corners)나 가장자리(Edges)에 글자를 배치하지 마십시오. 글자는 반드시 중앙 피사체 주변에만 연출하십시오.


    4. 공간 암시 컷 (Contextual Hint):**
    - **상황:** 사건의 장소가 중요할 때.
    - **연출:** 화면을 꽉 채우는 배경 그림은 금지입니다. 대신, 그 장소를 상징하는 **'최소한의 랜드마크'**나 **'구조적 요소(기둥, 창문, 지평선)'** 하나만을 캐릭터 뒤에 배치하여 공간감을 **'암시'**만 하십시오. (예: 실내라면 벽 전체가 아니라 창문 하나만 그리기)

    5. **[구도]:** 분할 화면 금지. **{target_layout}**.

    [9:16 세로 모드 지침]
    - 인물 중심일 땐 상반신 클로즈업.
    - 공간 연출 시에는 천장(조명)이나 바닥(가구)을 활용해 수직적 공간감을 주십시오.

    [임무]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    대본을 보고 **'인물/사물만 강조할지'** 아니면 **'심플한 배경을 넣어줄지'** 판단하여 **History Matters 스타일의 프롬프트**를 작성하십시오.
    - **필수 키워드:** "History Matters style, OverSimplified style, minimalism, thick black outlines, flat colors, simple background context, funny expressions, vector art"
    - **한글**로만 출력하십시오.
    - (지문) 같은 부연설명 연출 지시어는 제외한다.
        """

    # ---------------------------------------------------------
    # [모드 6] 실사 + 코믹 페이스 (Hyper Realism + Comic Face) - [NEW! 수정됨]
    # ---------------------------------------------------------
    elif genre_mode == "comic_realism":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **'고퀄리티 실사 배경에 우스꽝스러운 합성을 하는 초현실주의 아티스트'**입니다.
    마치 내셔널 지오그래픽 다큐멘터리 장면에 유머러스한 스티커를 붙인 듯한 '병맛(Bizarre Humor)' 이미지를 만듭니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **[베이스: 극도로 사실적인 실사 (Hyper-Realism)]:**
        - **배경(Background) & 몸체(Body):** 무조건 **'Unreal Engine 5 Render', '8K Photograph', 'Cinematic Lighting'** 스타일이어야 합니다.
        - 동물의 털, 사람의 옷 주름, 피부 질감, 주변 환경(숲, 도시 등)은 사진처럼 리얼해야 합니다.

    2. **[반전 포인트 1: 사람 얼굴 (Human Face)]:**
        - 눈 (Eyes): 완벽한 원형의 흰자위에 작은 점으로 표현된 눈동자(Dot pupils)가 특징입니다. 이는 **'릭 앤 모티(Rick and Morty)'**와 같은 서양 애니메이션에서 당황하거나 멍청해 보이는 표정을 연출할 때 자주 쓰는 기법입니다.
        - 몸과 행동은 진지하고 사실적이다.
        - **Face Style Keywords:** "Simple 2D cartoon face pasted on real body", "Exaggerated expression with bold lines".
        - 윤곽선 (Outlines): 굵기가 일정한 검은색 라인으로 단순하게 처리되었습니다. 명암이나 질감 묘사가 전혀 없는 전형적인 2D 드로잉 방식입니다.
        - 채색 (Coloring): 그라데이션이나 그림자 없이 단색(Flat color)으로 채워져 있다.
          
    3. **[반전 포인트 2: 동물 눈 (Animal Eyes)]:**
        - 맘모스, 사자, 공룡 등 위협적인 동물이라도 **눈(Eyes)은 반드시 '단순한 2D 만화 눈'**이어야 합니다.
        - **Eye Style Keywords:** "2D cartoon eyes", "Simple white sclera with black dot pupils", "Silly expression".
        - **[참조 스타일]** 제공된 매머드 이미지처럼, 실사 눈 대신 **흰색 흰자와 검은색 점 눈동자로 된 단순한 만화 눈**을 적용하십시오.

    4. **조명 및 분위기:** - 조명은 **매우 진지하고 웅장하게(Cinematic & Epic)** 연출하여, 우스꽝스러운 얼굴과 대비를 극대화하십시오.
      
    5. **[텍스트]:** {lang_guide} {lang_example}
        - [필수] 텍스트는 간판 이런게 아닌이상 거의 연출하지 않는다. 특히 그래픽 같이 자연스럽지 않게 텍스트는 절대 나오지 않는다.
        - 말풍선 연출하지 않는다.

    [🎭 대본 연출 및 행동 지침 (Action & Storytelling) - 중요]
    캐릭터가 단순히 서 있는 정적인 장면은 피하십시오. **대본 내용을 '온몸으로' 연기해야 합니다.**
    - 캐릭터의 **몸(Body)**은 헐리우드 액션 영화나 비극적인 다큐멘터리 주인공처럼 **매우 진지하고 역동적인 포즈**를 취해야 합니다. (예: 절규하며 무릎 꿇기, 다급하게 도망치기, 비장하게 지휘하기)
    - 대본을 표현하는 동물들의 행동 연출 극대화.

    [🚨 9:16 세로 모드 필수 지침 (Vertical Layout) 🚨]
    - **환경(Environment)보다 캐릭터(Character)가 우선입니다.**
    - 광활한 초원을 멀리서 찍지 마십시오. (캐릭터가 점으로 보이면 실패입니다.)
    - **구도:** 카메라 렌즈를 캐릭터 코앞까지 가져오십시오 (Extreme Close-up / Selfie angle).
    - **치타/동물:** 동물이 화면 밖으로 튀어나올 듯이 **정면으로 달려오는 구도**나, **얼굴이 화면에 적당히 차는 구도**를 묘사하십시오.
    - 배경은 캐릭터 뒤로 흐릿하게 날아가거나(Depth of field), 위아래로 뻗은 나무/건물/빙하/우주/눈/도시 등을 이용해 수직감을 주십시오.

    [임무]
    대본을 분석하여 위 스타일이 적용된 프롬프트를 작성하십시오.
    - **필수 키워드 포함:** "Photorealistic 8k render, Unreal Engine 5, Cinematic lighting, Funny 2D cartoon face on realistic body, 2D cartoon eyes (white sclera, black dot pupil) on animal, Visual comedy, Meme style collage, Vertical Portrait Composition, Close-up"
    - **상황 연출:** 대본의 심각한 상황(예: 멸종, 전쟁)을 묘사하되, 캐릭터들의 표정은 멍청하거나(Derp) 과장되게 묘사하십시오.
    - (지문) 같은 부연설명 연출 지시어는 제외한다.
    - **한글**로만 작성하십시오.
        """

    # ---------------------------------------------------------
    # [모드 7] 핑크 3D 해골 (Pink Translucent Skull) - [UPDATED!]
    # ---------------------------------------------------------
    elif genre_mode == "pink_skull":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **'Helix' 채널 스타일의 3D 아티스트**입니다.
    기괴하지만 유머러스한 **'투명한 플라스틱/유리 재질의 해골'**이 등장하여 대본의 상황을 연기합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **[필수 - 배경] 무조건 '단색 핑크 배경 (Solid Pink Background)'**:
        - 배경은 복잡한 풍경이 아니라, **균일한 분홍색(#FFC0CB ~ #FF69B4)** 스튜디오 배경이어야 합니다.
        - 가구(소파, 의자) 외에는 배경에 불필요한 사물을 두지 마십시오.

    2. **[필수 - 캐릭터] 투명/반투명 해골 (Translucent Skeleton)**:
        - **재질:** 겉은 매끄러운 투명 플라스틱/유리 재질이지만, **'내부의 뼈 구조(Internal Bone Structure)'**가 은은하고 디테일하게 비쳐 보여야 합니다. (단순한 투명 덩어리 X)
        - **눈(Eyes) - 가장 중요:** - 해골의 눈구멍이 비어있으면 절대 안 됩니다. 
            - 반드시 **'선명한 하얀색 눈알(Bright White Eyeballs)'**을 끼워 넣으십시오.
            - 눈알 위에는 **작은 검은색 동공(Small Black Pupils)**을 그려 넣어, **멍청하거나(Goofy) 놀란 표정**을 명확히 만드십시오.

    3. **[필수 - 자세 및 가구 (Pose & Furniture)]**:
        - **기본 자세:** 해골은 공중에 떠 있는 것이 아니라, **'푹신한 소파(Sofa)', '고급 가죽 의자', '책상(Desk)'** 등에 **앉아 있는(Sitting)** 구도를 우선적으로 사용하십시오.
        - 상황이 역동적일 때만 서 있거나(Standing) 움직이는 자세를 취하십시오.
        - 가구 묘사: 소파의 주름, 책상의 나무 질감 등 가구는 매우 사실적(Photorealistic)이어야 합니다.

    4. **[소품 및 연출]**:
        - 해골이 대본에 나오는 **음식, 돈, 스마트폰, 게임기 등을 손에 들고 있거나 책상 위에 올려두어야 합니다.**
        - 소품은 핑크 배경과 대비되는 **채도 높은 색상**으로 사실적으로 묘사하십시오.

    5. **[조명 및 렌더링]**:
        - **"Blender 3D, Octane Render, High Glossy, Subsurface Scattering"**.
        - 해골의 투명한 재질과 눈알이 반짝이도록 **밝고 쨍한 스튜디오 조명**을 사용하십시오.

    6. **[텍스트]**: {lang_guide} {lang_example}
        - 텍스트는 해골 옆 공간이나, 해골이 들고 있는 팻말에 자연스럽게 배치하십시오.
        - 텍스트는 거의 나오지 않는다. 나와도 자연스럽게 배경과 어울리게 연출한다. 간판이나 사물에.
        - 절대 그래픽 같은 연출로 텍스트를 쓰지 않는다.

    [9:16 세로 모드 지침]
    - 해골이 의자에 앉아 있는 모습이 잘리거나 작아 보이지 않게, **'무릎 위 상반신(Medium Shot)'**이나 **'얼굴과 상체(Close-up)'** 위주로 꽉 차게 잡으십시오.

    [임무]
    대본을 분석하여 위 스타일이 적용된 프롬프트를 작성하십시오.
    - **필수 키워드:** "3D render, Translucent clear plastic human skeleton with visible internal bones, Funny Googly eyes, Sitting on a sofa/chair, Solid Pink background, Studio lighting"
    - **한글**로만 작성하십시오.
        """

    # ---------------------------------------------------------
    # [모드 8] 웹툰 (K-Webtoon Style) - [NEW!]
    # ---------------------------------------------------------
    elif genre_mode == "webtoon":
        full_instruction = f"""
    {common_header}
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

    # ---------------------------------------------------------
    # [모드 9] 만화 (High-Budget Anime) - [NEW!]
    # ---------------------------------------------------------
    elif genre_mode == "manga":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **작화 퀄리티가 극도로 높은 '대작 귀여운 지브리풍 애니메이션'의 총괄 작화 감독**입니다.
    단순히 예쁜 그림이 아니라, **대본의 상황, 행동, 감정을 '소름 돋을 정도로 구체적이고 디테일하게' 묘사**해야 합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [필수 연출 지침]
    1. **작화 스타일 (High Detail):**
        - **서정적이고 몽환적인 느낌 금지.** 대신 **선명하고, 사실적이니지만 인물은 귀여운, 정보량이 많은(High Information Density)** 작화를 추구하십시오.
        - 배경은 흐릿하게 처리하지 말고, 간판의 글씨, 책상의 소품, 벽의 질감까지 **집요할 정도로 디테일하게** 묘사하십시오. (예: 'MAPPA', 'Ufotable' 제작사의 고퀄리티 작화 스타일)
    2. **행동 및 감정 묘사 (Action & Emotion):**
        - 대본에 묘사된 캐릭터의 행동을 **'순간 포착'** 하듯 역동적으로 그리십시오.
        - **표정 연기:** 눈썹의 각도, 입 모양, 눈동자의 흔들림까지 구체적으로 지시하여 캐릭터의 심리를 완벽하게 표현하십시오.
    3. **대본 충실도 (Script Fidelity):**
        - 대본에 있는 작은 지문 하나도 놓치지 말고 시각화하십시오.
        - "컵을 떨군다"는 대본이라면, 컵이 손에서 떠나 공중에 있는 순간과 튀어 오르는 물방울까지 묘사하십시오.
    4. **텍스트 처리:** {lang_guide} {lang_example}
        
    [작성 요구사항]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - 절대 분활화면 연출하지 않는다. 전체 대본 내용에 어울리는 하나의 장면으로 묘사.

    [임무]
    대본을 분석하여 AI가 그릴 수 있는 **최상급 귀여운 지브리풍 퀄리티의 애니메이션 프롬프트**를 작성하십시오.
    - "지브리 풍 Masterpiece, best quality, ultra-detailed, intricate background, dynamic pose, expressive face" 등의 키워드가 반영되도록 하십시오.
    - '대작 귀여운 지브리풍 애니메이션' 필수로 키워드 반영.
    - **한글**로만 출력하십시오.
        """

    # ---------------------------------------------------------
    # [모드 10] AI Reconstruction (건축/복원/시대재현) - [NEW!]
    # ---------------------------------------------------------
    elif genre_mode == "reconstruction":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **'역사적 고증과 건축 시각화(Architectural Visualization)'를 전문으로 하는 AI 아티스트**입니다.
    대본에 묘사된 장소의 **'과거, 현재, 혹은 미래의 모습'**을 마치 타임머신을 타고 가서 찍은 **고화질 사진(Photorealistic)**처럼 복원해야 합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [핵심 비주얼 스타일 가이드 - 절대 준수]
    1. **화풍 (Art Style):** - 무조건 **'실사(Photorealistic)', '8K Resolution', 'Unreal Engine 5 Lumen Render'**.
        - 그림, 만화, 일러스트 느낌이 나면 안 됩니다. **완벽한 사진**이어야 합니다.
     
    2. **건축 및 환경 (Architecture & Environment):**
        - 이 모드의 주인공은 **'장소(Place)'**입니다.
        - 건물의 재질(벽돌의 깨짐, 나무의 결, 금속의 녹슴), 도로의 상태(포장도로, 흙길, 빗물 고인 웅덩이), 하늘의 날씨 등을 집요하게 묘사하십시오.
        - **시대적 고증(Historical Accuracy):** 대본이 1900년대를 말하면 그 시대의 간판, 가로등, 자동차, 마차 등을 정확히 배치하십시오.
        - **장소의 변화:** 대본 내용에 따라 건물이 지어지는 중이거나, 파괴되었거나, 번영하는 모습을 극적으로 표현하십시오.

    3. **인물 및 군중 (People & Crowd):**
        - 인물은 **'자연스러운 배경'**처럼 연출하십시오. 카메라를 의식하고 포즈를 취하는 것이 아니라, 그 시대의 옷을 입고 **일상을 살아가는 모습(Walking, Talking, Working)**이어야 합니다.
        - 인물보다는 **'인물이 있는 풍경'**이 중요합니다.
     
    4. **카메라 앵글 (Camera Angle):**
        - 웅장함을 보여주는 **'광각(Wide Angle)'**, 거리의 깊이감을 주는 **'소실점 구도(Vanishing Point)'**, 혹은 전체를 조망하는 **'드론 샷(Drone Shot)'**을 적극 활용하십시오.

    5. **조명 (Lighting):**
        - 인공적인 스튜디오 조명이 아닌, **자연광(Natural Sunlight, Overcast, Sunset)**을 사용하여 사실감을 극대화하십시오.
        - **대기 원근법(Atmospheric Perspective)**과 안개(Fog)를 사용하여 공간의 깊이를 만드십시오.

    6. **텍스트 처리:** {lang_guide} {lang_example}
        - 텍스트는 옛날 간판, 포스터, 현수막 등 **건축물과 환경에 자연스럽게 녹아든 형태**로만 연출하십시오. 인위적인 자막은 금지입니다.

    [9:16 세로 모드 지침]
    - 높은 건물의 **수직감(Verticality)**을 강조하거나, 좁은 골목길의 **깊이감(Depth)**을 표현하는 구도를 사용하십시오.
    - 바닥부터 하늘까지 꽉 차게 묘사하십시오.

    [임무]
    대본을 분석하여, 그 시대와 장소를 완벽하게 복원하는 **'초고화질 건축 시각화 프롬프트'**를 작성하십시오.
    - **필수 키워드:** "Hyper-realistic, 8k, Unreal Engine 5 render, Architectural visualization, Historical reconstruction, Detailed texture, Volumetric lighting"
    - **한글**로만 작성하십시오.
        """

    else: # Fallback
        full_instruction = f"스타일: {style_instruction}. 비율: {target_layout}. 대본 내용: {text_chunk}. 이미지 프롬프트 작성."

    # 공통 실행 로직 (503 에러 방지 및 재시도 로직 강화)
    payload = {
        "contents": [{"parts": [{"text": f"Instruction:\n{full_instruction}\n\nScript Segment:\n\"{text_chunk}\"\n\nImage Prompt (Korean Only, Safe for Work):"}]}]
    }

    max_retries = 3  # 재시도 횟수
    
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            
            if response.status_code == 200:
                try:
                    prompt = response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # [안전장치] 9:16일 경우 프롬프트 앞단에 강제 주입
                    if "9:16" in target_layout:
                          prompt = "Vertical 9:16 smartphone wallpaper composition, Close-up shot, Portrait mode, (세로 화면 꽉 찬 구도), " + prompt
                          
                    # 금지어 후처리
                    banned_words = ["피가", "피를", "시체", "절단", "학살", "살해", "Blood", "Kill", "Dead"]
                    for bad in banned_words:
                        prompt = prompt.replace(bad, "")
                    
                    return (scene_num, prompt) # 성공 시 반환
                except:
                    # JSON 파싱 실패 시 원본 사용
                    return (scene_num, text_chunk)

            # 503(Service Unavailable) 또는 500번대 에러인 경우 -> 잠시 대기 후 재시도
            elif response.status_code in [500, 502, 503, 504]:
                time.sleep(2 + attempt) # 2초, 3초... 늘려가며 대기
                continue # 다음 시도로 넘어감

            # 429(Too Many Requests) -> 대기 후 재시도
            elif response.status_code == 429:
                time.sleep(5)
                continue 
            
            else:
                # 재시도하지 않는 에러
                return (scene_num, f"API_ERROR_CODE: {response.status_code}")

        except Exception as e:
            if attempt == max_retries - 1: # 마지막 시도
                return (scene_num, f"API_ERROR_CONN: {e}")
            time.sleep(2)

    # 모든 재시도 실패 시 (사용자가 이해할 수 있는 에러 메시지 반환)
    return (scene_num, f"API_ERROR: 지금은 구글 AI 서버 사용량이 많아 프롬프트를 만들지 못했습니다. (503 Error)")

# ==========================================
# [함수] 3. 이미지 생성 (API 제한 대응)
# ==========================================
def generate_image(client, prompt, filename, output_dir, selected_model_name, target_ratio="16:9"):
    full_path = os.path.join(output_dir, filename)
    max_retries = 5
    last_error_msg = "알 수 없는 오류" 

    # 안전 필터 설정
    safety_settings = [
        types.SafetySetting(
            category="HARM_CATEGORY_DANGEROUS_CONTENT",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HARASSMENT",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_HATE_SPEECH",
            threshold="BLOCK_ONLY_HIGH"
        ),
        types.SafetySetting(
            category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
            threshold="BLOCK_ONLY_HIGH"
        ),
    ]

    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=selected_model_name,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(aspect_ratio=target_ratio),
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
            
            last_error_msg = "이미지 데이터 없음 (Blocked by Safety Filter?)"
            print(f"⚠️ [시도 {attempt}/{max_retries}] {last_error_msg} ({filename})")
            time.sleep(2)
            
        except Exception as e:
            error_msg = str(e)
            last_error_msg = error_msg
            
            if "429" in error_msg or "ResourceExhausted" in error_msg:
                wait_time = (2 * attempt) + random.uniform(0.5, 2.0)
                print(f"🛑 [API 제한] {filename} - {wait_time:.1f}초 대기 후 재시도... (시도 {attempt})")
                time.sleep(wait_time)
            else:
                print(f"⚠️ [에러] {error_msg} ({filename}) - 5초 대기")
                time.sleep(5)
            
    print(f"❌ [최종 실패] {filename}")
    return f"ERROR_DETAILS: {last_error_msg}"

# ==========================================
# [UI] 사이드바 (설정)
# ==========================================
with st.sidebar:
    st.header("⚙️ 환경 설정")
    
    # API Key 직접 입력
    api_key = st.text_input("🔑 Google API Key (직접 입력)", type="password")

    st.markdown("---")
    
    st.subheader("🖼️ 이미지 모델 선택")
    model_choice = st.radio("사용할 AI 모델:", ("Premium (Gemini 3 Pro)", "Fast (Gemini-2.5-pro)"), index=0)
    
    if "Gemini 3 Pro" in model_choice:
        SELECTED_IMAGE_MODEL = "gemini-3-pro-image-preview" 
    else:
        SELECTED_IMAGE_MODEL = "gemini-2.5-flash-image"

    st.info(f"✅ 선택 모델: `{SELECTED_IMAGE_MODEL}`")
    
    st.markdown("---")
    st.subheader("📐 화면 비율 선택")
    ratio_selection = st.radio(
        "영상 화면 비율:",
        ("16:9 (유튜브 가로형)", "9:16 (쇼츠/릴스 세로형)"),
        index=0
    )

    if "9:16" in ratio_selection:
        TARGET_RATIO = "9:16"
        LAYOUT_KOREAN = """
        [9:16 Vertical Portrait Mode]
        - 이 이미지는 세로로 긴 스마트폰 배경화면 비율입니다.
        - 절대 가로로 넓은 광각(Wide angle) 구도를 잡지 마십시오.
        - **세로형 포트레이트(Vertical Portrait)** 구도를 사용하여, 피사체(인물/동물)가 화면의 좌우를 꽉 채우도록 '클로즈업(Close-up)' 하십시오.
        - 머리부터 허리까지 보여주는 '미디엄 샷' 또는 얼굴이 꽉 차는 '클로즈업'을 사용하십시오.
        """
    else:
        TARGET_RATIO = "16:9"
        LAYOUT_KOREAN = "16:9 와이드 비율."

    st.markdown("---")
    # [복구됨] 장면 분할(시간) 슬라이더
    st.subheader("⏱️ 장면 분할 설정")
    chunk_duration = st.slider("한 장면당 예상 지속 시간 (초)", 5, 60, 20, 5, help="이 시간을 기준으로 대본을 자릅니다. (예: 20초 = 약 160자)")
    chars_limit = chunk_duration * 8 # 초당 8글자 기준
    st.caption(f"💡 {chunk_duration}초 = 약 {chars_limit}자 단위로 대본을 자릅니다.")
    
    st.markdown("---")
    # ---------------------------------------------------------------------------
    # 스마트 장르 선택 & 직접 입력 로직
    # ---------------------------------------------------------------------------
    st.subheader("🎨 영상 장르(Mood) 설정")

    # 프리셋 정의
    PRESET_INFO = """대사에 어울리는 2d 얼굴이 둥근 하얀색 스틱맨 연출로 설명과 이해가 잘되는 느낌으로 그려줘 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로 너무 어지럽지 않게, 글씨는 핵심 키워드 2~3만 나오게 한다.
글씨가 너무 많지 않게 핵심만. 2D 스틱맨을 활용해 대본을 설명이 잘되게 설명하는 연출을 한다. 자막 스타일 연출은 하지 않는다.
글씨가 나올경우 핵심 키워드 중심으로만 나오게 너무 글이 많지 않도록 한다, 글자는 배경과 사물에 자연스럽게 연출, 전체 배경 연출은 2D로 디테일하게 입체적이고 몰입감 있게 연출해서 그려줘 (16:9).
다양한 장소와 상황 연출로 배경을 디테일하게 한다. 무조건 2D 스틱맨 연출."""
    
    PRESET_REALISTIC = """고퀄리티 얼구이 둥근 2D 애니메이션 스타일, 사실적인 배경과 조명 연출.
캐릭터: 얼굴이 둥근 하얀색 2D 스틱맨들. 단순한 낙서가 아니라, 명암과 덩어리감이 느껴지는 '고급 스틱맨' 스타일. 얼굴이 크게 잘보이게 연출.
배경: 단순한 단색 배경 금지. 대본의 장소(사무실, 거리, 방 안, 전장 등)를 '사진'처럼 디테일하고 입체적으로 2d 묘사.
분위기: 정보 전달보다는 '상황극(Drama)'에 집중. 영화적인 조명(Cinematic Lighting)과 심도(Depth) 표현.
연출: 스틱맨 여러 캐릭터들이 대본 속 행동을 리얼하게 연기(Acting). 감정 표현은 표정보다는 역동적인 몸짓(Body Language)으로 극대화.
절대 금지: 화면 분할(Split Screen), 텍스트 나열, 단순 인포그래픽 스타일.
대본의 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로 연출."""

    PRESET_HISTORY = """역사적 사실을 기반으로 한 '2D 시네마틱 얼굴이 둥근 하얀색 스틱맨 애니메이션' 스타일.
깊이 있는 색감(Dark & Rich Tone)과 극적인 조명 사용.
캐릭터는 2D 실루엣이나 스틱맨이지만 시대에 맞는 의상과 헤어스타일을 착용.
2D 스틱맨을 활용해 대본을 설명이 잘되게 설명하는 연출을 한다. 자막 스타일 연출은 하지 않는다.
전쟁, 기근 등의 묘사는 상징적이고 은유적으로 표현. 너무 고어틱한 연출은 하지 않는다.
배경 묘사에 디테일을 살려 시대적 분위기를 강조. 무조건 얼굴이 둥근 2D 스틱맨 연출.
대본의 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로 연출."""

    PRESET_3D = """Unreal Engine 5 render style, Realistic 3D game cinematic screenshot.
피사체: 매끈하고 하얀 이목구비 없는 마네킹 머리 (Smooth white featureless mannequin head). 눈코입 없음.
복장: 가디건, 청바지, 정장 등 현실적인 의상을 입혀 기묘한 느낌 강조.
조명: 영화 같은 조명 (Cinematic lighting), 다소 어둡고 분위기 있는(Moody) 연출.
배경: 낡은 소파, 어지러진 방 등 사실적인 텍스처와 디테일(8k resolution), 현실적인 다양한 장소.
대본의 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로 연출."""

    PRESET_SCIFI = """3D Technical Animation (Fern, AiTelly Style).
화풍: Blender Cycles / Clean Rendering, 밝은 스튜디오 조명(Clean Studio Lighting).
연출: 기계/건축물의 단면도(Cutaway) 및 작동 원리 시각화.
인물: 엔지니어/과학자/교사/회사원/군인 등등 다양한 3d 캐릭터가 등장하여 기계를 조작하거나 설명하는 기능적 역할 수행.
분위기: 깔끔하고, 교육적이며, 명확함(Clear & Educational). 과도한 그림자 배제.
대본의 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로 연출."""

    PRESET_PAINT = """'History Matters' & 'OverSimplified' 스타일 (Clean & Focused Minimalism).
핵심 원칙: **"한 장면에 오직 하나의 주제만(Single Focus)"** 담백하게 연출. 복잡한 합성 금지.
화풍: 굵은 검은색 외곽선, 명암 없는 플랫 컬러, 둥근 머리 스틱맨.
연출: 인물 중심일 땐 인물 연기에만, 장소 중심일 땐 건물만, 사물 중심일 땐 물건만 **큼직하고 단순하게** 묘사.
텍스트: 굵은 마카펜 손글씨 느낌. 꼭 필요한 라벨링만 최소화하여 배치. 화면 모서리 주변에 텍스트 연출하지 않는다.
배경: 단색 배경이나 여백을 최대한 살려 피사체 하나에만 집중되도록 구성. 배경은 기본적으로 하얀색 이지만 상황에 따라 다른색 이용.
전체 대본에 어울리는 하나의 장면으로 연출.
(지문) 같은 부연설명 연출 지시어는 제외한다."""

    PRESET_COMIC_REAL = """Hyper-Realistic Environment with Comic Elements.
배경과 사물, 사람/동물의 몸체: '언리얼 엔진 5' 수준의 8K 실사(Photorealistic). 털, 피부 질감, 조명 완벽 구현.
사람 얼굴: 몸은 실사지만 얼굴만 '릭 앤 모티(Rick and Morty) 애니메이션 스타일'의 2D 카툰으로 합성. (참조: 큰 흰색 눈, 검은 점 눈동자, 굵은 눈썹, 단순한 입).
- **표정:** 당황, 공포, 혼란, 술에 취한 듯한 '병맛' 표정 강조.
동물 눈: 털과 몸은 다큐멘터리급 실사지만, 눈만 '흰색 흰자와 검은 점 눈동자'로 된 2D 만화 눈으로 연출.
분위기: 고퀄리티 다큐멘터리인 척하는 병맛 코미디. 진지한 상황일수록 표정을 더 단순하고 멍청하게(Derp) 연출.
절대 이미지에 글씨 연출 전혀 하지 않는다."""

    PRESET_SKULL = """3D Render, Translucent Plastic Skeleton, Solid Pink Background.
[캐릭터 외형]
- 재질: 투명한 플라스틱/유리(Translucent Clear Plastic). 속이 투명하지만 **내부 뼈대의 구조와 윤곽**은 뚜렷하게 보여야 함.
- 되도록 상체는 무조건 연출해야한다.
- **눈(Eyes):** 텅 빈 눈구멍 절대 금지. **'선명하고 하얀 눈동자(Bright White Eyeballs)'**가 박혀 있어야 함. (검은색 작은 동공). 멍청하고 우스꽝스러운 표정 필수.[자세 및 연출]
- **자세(Pose):** 기본적으로 **'소파(Sofa)'나 '책상(Desk) 의자'에 앉아있는(Sitting)'** 모습 위주. (상황에 따라 서 있거나 춤추는 연출 가능).
- 거만하거나 힙(Hip)하게 걸터앉은 자세.
[소품 및 배경]
- 가구: 벨벳 소파, 게이밍 의자, 고급 책상 등 가구의 디테일한 묘사.
- 소품: 대본 속 물건(돈, 음식, 기계)을 사실적으로 표현.
- 배경: 무조건 **'단색 핑크(Solid Pink)'** 유지.
[텍스트] 텍스트는 거의 연출하지 않는다. """

    PRESET_WEBTOON = """한국 인기 웹툰 스타일의 고퀄리티 2D 일러스트레이션 (Korean Webtoon Style).
선명한 펜선과 화려한 채색. 집중선(Speed lines)은 정말 중요한 순간에만 가끔 사용.
캐릭터는 8등신 웹툰 주인공 스타일. 캐릭터 주변의 '상황'과 '배경(장소)'을 아주 구체적이고 밀도 있게 묘사.
단순 인물 컷보다는 주변 사물과 배경이 함께 보이는 구도 선호. 
전체적으로 배경 디테일이 살아있는 네이버 웹툰 썸네일 스타일. (16:9)"""

    PRESET_MANGA = """일본 대작 귀여운 지브리풍 애니메이션 스타일 (High-Budget Anime Style).
서정적인 느낌보다는 '정보량이 많고 치밀한' 고밀도 배경 작화 (High Detail Backgrounds).
지브리 캐릭터의 표정과 행동을 '순간 포착'하듯 역동적으로 묘사.
대본의 지문을 하나도 놓치지 않고 시각화하는 '철저한 디테일' 위주. (16:9)
전체 대본에 어울리는 하나의 장면으로 연출."""

    # [NEW] AI Reconstruction 프리셋 추가
    PRESET_RECONSTRUCTION = """[AI Reconstruction / Architectural Visualization]
과거, 현재, 미래의 특정 장소를 '완벽한 고증과 사실감'으로 복원(Reconstruction)하는 스타일.
화풍: National Geographic 역사 다큐멘터리 사진, 8K Unreal Engine 5 Architectural Render.
핵심 대상: 건축물(Architecture), 거리(Street), 환경(Environment), 시대적 분위기(Atmosphere).
인물: 인물은 카메라를 보지 않고 그 시대의 일상 생활을 하는 '자연스러운 군중'으로 연출.
조명: 자연광(Sunlight), 날씨 표현, 건물의 질감(벽돌, 나무, 콘크리트)을 극대화하는 라이팅.
대본의 시대와 장소를 완벽하게 시각화하여, 마치 그 장소에 실제로 와 있는 듯한 현장감 부여."""

    # 세션 상태 초기화
    if 'style_prompt_area' not in st.session_state:
        st.session_state['style_prompt_area'] = PRESET_INFO
    
    # 옵션 리스트 정의
    OPT_INFO = "밝은 정보/이슈 (Bright & Flat)"
    OPT_REALISTIC = "스틱맨 드라마/사실적 연출 (Realistic Storytelling)"
    OPT_HISTORY = "역사/다큐 (Cinematic & Immersive)"
    OPT_3D = "3D 다큐멘터리 (Realistic 3D Game Style)"
    OPT_SCIFI = "과학/엔지니어링 (3D Tech & Character)"
    OPT_PAINT = "심플 그림판/졸라맨 (The Paint Explainer Style)"
    OPT_COMIC_REAL = "실사 + 코믹 페이스 (Hyper Realism + Comic Face)"
    OPT_CUSTOM = "직접 입력 (Custom Style)"
    OPT_SKULL = "핑크 3D 해골 (Helix Style Pink Skeleton)"
    OPT_WEBTOON = "한국 웹툰 스타일 (K-Webtoon Style)"
    OPT_MANGA = "지브리풍 대작 애니메이션 (High-Budget Anime)"
    
    # [NEW] 옵션 이름 추가
    OPT_RECONSTRUCTION = "AI 복원/건축 (AI Reconstruction)" 

    def update_text_from_radio():
        selection = st.session_state.genre_radio_key
        if selection == OPT_INFO:
            st.session_state['style_prompt_area'] = PRESET_INFO
        elif selection == OPT_REALISTIC:
            st.session_state['style_prompt_area'] = PRESET_REALISTIC
        elif selection == OPT_HISTORY:
            st.session_state['style_prompt_area'] = PRESET_HISTORY
        elif selection == OPT_3D:
            st.session_state['style_prompt_area'] = PRESET_3D
        elif selection == OPT_SCIFI: 
            st.session_state['style_prompt_area'] = PRESET_SCIFI
        elif selection == OPT_PAINT:
            st.session_state['style_prompt_area'] = PRESET_PAINT
        elif selection == OPT_COMIC_REAL:
            st.session_state['style_prompt_area'] = PRESET_COMIC_REAL
        elif selection == OPT_SKULL:
            st.session_state['style_prompt_area'] = PRESET_SKULL
        elif selection == OPT_WEBTOON:
            st.session_state['style_prompt_area'] = PRESET_WEBTOON
        elif selection == OPT_MANGA:
            st.session_state['style_prompt_area'] = PRESET_MANGA
        # [NEW] 라디오 버튼 선택 시 텍스트 업데이트 로직 추가
        elif selection == OPT_RECONSTRUCTION:
            st.session_state['style_prompt_area'] = PRESET_RECONSTRUCTION

    def set_radio_to_custom():
        st.session_state.genre_radio_key = OPT_CUSTOM

    genre_select = st.radio(
        "콘텐츠 성격 선택:",
        # [NEW] 리스트에 OPT_RECONSTRUCTION 추가
        (OPT_INFO, OPT_REALISTIC, OPT_HISTORY, OPT_3D, OPT_SCIFI, OPT_PAINT, OPT_COMIC_REAL, OPT_SKULL, OPT_WEBTOON, OPT_MANGA, OPT_RECONSTRUCTION, OPT_CUSTOM),
        index=0,
        key="genre_radio_key",
        on_change=update_text_from_radio,
        help="텍스트를 직접 수정하면 자동으로 '직접 입력' 모드로 전환됩니다."
    )
    
    if genre_select == OPT_INFO: SELECTED_GENRE_MODE = "info"
    elif genre_select == OPT_REALISTIC: SELECTED_GENRE_MODE = "realistic_stickman"
    elif genre_select == OPT_HISTORY: SELECTED_GENRE_MODE = "history"
    elif genre_select == OPT_3D: SELECTED_GENRE_MODE = "3d_docu"
    elif genre_select == OPT_SCIFI: SELECTED_GENRE_MODE = "scifi"
    elif genre_select == OPT_PAINT: SELECTED_GENRE_MODE = "paint_explainer"
    elif genre_select == OPT_COMIC_REAL: SELECTED_GENRE_MODE = "comic_realism"
    elif genre_select == OPT_SKULL: SELECTED_GENRE_MODE = "pink_skull"
    elif genre_select == OPT_WEBTOON: SELECTED_GENRE_MODE = "webtoon"
    elif genre_select == OPT_MANGA: SELECTED_GENRE_MODE = "manga"
    # [NEW] 모드 매핑 추가
    elif genre_select == OPT_RECONSTRUCTION: SELECTED_GENRE_MODE = "reconstruction"
    else: SELECTED_GENRE_MODE = "info" # 기본값

    st.markdown("---")

    st.subheader("🌐 이미지 텍스트 언어")
    target_language = st.selectbox(
        "이미지 속에 들어갈 글자 언어:",
        ("Korean", "English", "Japanese"),
        index=0,
        help="이미지에 텍스트가 연출될 때 어떤 언어로 적을지 선택합니다."
    )

    st.markdown("---")

    st.subheader("🖌️ 화풍(Style) 지침")
    style_instruction = st.text_area(
        "AI에게 지시할 그림 스타일 (직접 수정 가능)", 
        key="style_prompt_area", 
        height=200,
        on_change=set_radio_to_custom 
    )

    st.markdown("---")
    max_workers = st.slider("작업 속도(병렬 수)", 1, 10, 5)

# ==========================================
# [UI] 메인 화면: 이미지 생성
# ==========================================
st.title("🎬 AI 씬(장면) 생성기 (Pro)")
st.caption(f"대본을 넣으면 장면별 이미지를 생성합니다. (이미지 전용 모드) | 🎨 Model: {SELECTED_IMAGE_MODEL}")

st.subheader("📌 전체 영상 테마(제목) 설정")

if 'video_title' not in st.session_state:
    st.session_state['video_title'] = ""
if 'title_candidates' not in st.session_state:
    st.session_state['title_candidates'] = []

col_title_input, col_title_btn = st.columns([4, 1])

# 제목 추천 로직
with col_title_btn:
    st.write("") 
    st.write("") 
    if st.button("💡 제목 5개 추천", type="primary", help="입력한 키워드나 대본을 바탕으로 제목을 추천합니다.", use_container_width=True):
        current_user_title = st.session_state.get('video_title', "").strip()
        
        if not api_key:
            st.error("API Key 필요")
        else:
            client = genai.Client(api_key=api_key)
            with st.spinner("AI가 최적의 제목을 고민 중입니다..."):
                prompt_instruction = f"""
                [Target Topic]
                "{current_user_title if current_user_title else 'No specific topic provided, suggest general viral titles'}"
                [Task]
                Generate 5 click-bait YouTube video titles.
                '몰락'이 들어간 경우 맨 뒤에 몰락으로 끝나게 한다.
                """
                
                title_prompt = f"""
                [Role] You are a YouTube viral marketing expert.
                {prompt_instruction}
                [Output Format]
                - Output ONLY the list of 5 titles.
                - No numbering (1., 2.), just 5 lines of text.
                - Language: Korean
                """
                
                try:
                    resp = client.models.generate_content(
                        model=GEMINI_TEXT_MODEL_NAME, 
                        contents=title_prompt
                    )
                    candidates = [line.strip() for line in resp.text.split('\n') if line.strip()]
                    clean_candidates = []
                    for c in candidates:
                        clean = re.sub(r'^\d+\.\s*', '', c).replace('*', '').replace('"', '').strip()
                        if clean: clean_candidates.append(clean)
                    
                    st.session_state['title_candidates'] = clean_candidates[:5]
                except Exception as e:
                    st.error(f"오류 발생: {e}")

with col_title_input:
    st.text_input(
        "영상 제목 (직접 입력하거나 우측 버튼으로 추천받으세요)",
        key="video_title", 
        placeholder="제목 혹은 만들고 싶은 주제를 입력하세요 (예: 부자들의 습관)"
    )

if st.session_state['title_candidates']:
    st.info("👇 AI가 추천한 제목입니다. 클릭하면 적용됩니다.")

    def apply_title(new_title):
        st.session_state['video_title'] = new_title
        st.session_state['title_candidates'] = [] 

    for idx, title in enumerate(st.session_state['title_candidates']):
        col_c1, col_c2 = st.columns([4, 1])
        with col_c1:
            st.markdown(f"**{idx+1}. {title}**")
        with col_c2:
            st.button(
                "✅ 선택", 
                key=f"sel_title_{idx}", 
                on_click=apply_title, 
                args=(title,), 
                use_container_width=True
            )
    
    if st.button("❌ 목록 닫기"):
        st.session_state['title_candidates'] = []

# 대본 입력창
if "image_gen_input" not in st.session_state:
    st.session_state["image_gen_input"] = ""

script_input = st.text_area(
    "📜 이미지로 만들 대본 입력", 
    height=300, 
    placeholder="대본을 직접 붙여넣으세요...",
    key="image_gen_input"
)

if 'generated_results' not in st.session_state:
    st.session_state['generated_results'] = []
if 'is_processing' not in st.session_state:
    st.session_state['is_processing'] = False

def clear_generated_results():
    st.session_state['generated_results'] = []

start_btn = st.button("🚀 이미지 생성 시작", type="primary", width="stretch", on_click=clear_generated_results)

if start_btn:
    if not api_key:
        st.error("⚠️ Google API Key를 입력해주세요.")
    elif not script_input:
        st.warning("⚠️ 대본을 입력해주세요.")
    else:
        st.session_state['generated_results'] = [] 
        st.session_state['is_processing'] = True
        
        # [수정] 폴더 초기화 (현재 사용자 폴더만)
        if os.path.exists(IMAGE_OUTPUT_DIR):
            try:
                shutil.rmtree(IMAGE_OUTPUT_DIR)
            except:
                pass
        init_folders()
        
        client = genai.Client(api_key=api_key)
        
        status_box = st.status("작업 진행 중...", expanded=True)
        progress_bar = st.progress(0)
        
        # 1. 대본 분할
        status_box.write(f"✂️ 대본 분할 중... (설정: 약 {chars_limit}자/장면)")
        chunks = split_script_by_time(script_input, chars_per_chunk=chars_limit)
        total_scenes = len(chunks)
        status_box.write(f"✅ {total_scenes}개 장면으로 분할 완료.")
        
        current_video_title = st.session_state.get('video_title', "").strip()
        if not current_video_title:
            current_video_title = "전반적인 대본 분위기에 어울리는 배경 (Context based on the script)"

        # 2. 프롬프트 생성 (병렬)
        status_box.write(f"📝 프롬프트 작성 중 ({GEMINI_TEXT_MODEL_NAME}) - 모드: {SELECTED_GENRE_MODE} / 비율: {TARGET_RATIO}...")
        prompts = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            
            for i, chunk in enumerate(chunks):
                futures.append(executor.submit(
                    generate_prompt, 
                    api_key, 
                    i, 
                    chunk, 
                    style_instruction, 
                    current_video_title, 
                    SELECTED_GENRE_MODE,
                    target_language,
                    LAYOUT_KOREAN
                ))
            
            for i, future in enumerate(as_completed(futures)):
                prompts.append(future.result())
                progress_bar.progress((i + 1) / (total_scenes * 2))
        
        prompts.sort(key=lambda x: x[0])
        
        # 3. 이미지 생성 (병렬 처리 + 속도 조절)
        status_box.write(f"🎨 이미지 생성 중 ({SELECTED_IMAGE_MODEL})... (API 보호를 위해 천천히 진행됩니다)")
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_meta = {}
            for s_num, prompt_text in prompts:
                idx = s_num - 1
                orig_text = chunks[idx]
                fname = make_filename(s_num, orig_text)
                
                # [🚨 핵심 수정] 프롬프트가 에러 메시지라면 이미지 생성을 시도하지 않음 (크레딧 보호)
                if prompt_text is None or "API_ERROR" in prompt_text or "Error_Connection" in prompt_text:
                    # 실패 결과 목록에 미리 추가 (이미지 생성 건너뜀)
                    results.append({
                        "scene": s_num,
                        "path": f"ERROR_DETAILS: {prompt_text}", # 여기에 친절한 한글 안내가 들어있음
                        "filename": fname,
                        "script": orig_text,
                        "prompt": "프롬프트 생성 실패로 인해 건너뜀"
                    })
                    continue # 다음 장면으로 넘어감

                time.sleep(0.1) 
                
                future = executor.submit(
                    generate_image, 
                    client, 
                    prompt_text, 
                    fname, 
                    IMAGE_OUTPUT_DIR, 
                    SELECTED_IMAGE_MODEL,
                    TARGET_RATIO 
                )
                future_to_meta[future] = (s_num, fname, orig_text, prompt_text)
            
            completed_cnt = 0
            for future in as_completed(future_to_meta):
                s_num, fname, orig_text, p_text = future_to_meta[future]
                
                result = future.result() 
                
                if result and "ERROR_DETAILS" not in result:
                    path = result
                    results.append({
                        "scene": s_num,
                        "path": path,
                        "filename": fname,
                        "script": orig_text,
                        "prompt": p_text
                    })
                else:
                    error_reason = result.replace("ERROR_DETAILS:", "") if result else "원인 불명 (None 반환)"
                    
                    if "429" in error_reason or "ResourceExhausted" in error_reason or "Quota" in error_reason:
                        st.error(f"🚨 Scene {s_num} 생성 실패! (일일 사용량 초과)")
                    elif "503" in error_reason or "ServiceUnavailable" in error_reason:
                        st.error(f"🚨 Scene {s_num} 생성 실패! (서버 과부하)")
                    else:
                        st.error(f"🚨 Scene {s_num} 실패!\n이유: {error_reason}")
                        
                    # 실패했어도 리스트에는 넣어서 UI에서 확인 가능하게 함
                    results.append({
                        "scene": s_num,
                        "path": f"ERROR_DETAILS: {error_reason}",
                        "filename": fname,
                        "script": orig_text,
                        "prompt": p_text
                    })

                completed_cnt += 1
                progress_bar.progress(0.5 + (completed_cnt / total_scenes * 0.5))
        
        results.sort(key=lambda x: x['scene'])
        st.session_state['generated_results'] = results
        
        status_box.update(label="✅ 완료되었습니다!", state="complete", expanded=False)
        st.session_state['is_processing'] = False
        
# ==========================================
# [UI] 결과창 및 개별 재생성 기능
# ==========================================
if st.session_state['generated_results']:
    st.divider()
    st.header(f"📸 결과물 ({len(st.session_state['generated_results'])}장)")
    
    # ------------------------------------------------
    # 1. 일괄 작업 버튼 영역
    # ------------------------------------------------
    st.write("---")
    st.subheader("⚡ 원클릭 일괄 다운로드")
    
    zip_data = create_zip_buffer(IMAGE_OUTPUT_DIR)
    st.download_button("📦 전체 이미지 ZIP 다운로드", data=zip_data, file_name="all_images.zip", mime="application/zip", use_container_width=True)

    # ------------------------------------------------
    # 2. 개별 리스트 및 [재생성] 기능
    # ------------------------------------------------
    for index, item in enumerate(st.session_state['generated_results']):
        with st.container(border=True):
            cols = st.columns([1, 2])
            
            # [왼쪽] 이미지 및 재생성 버튼
            with cols[0]:
                # [수정] 경로에 ERROR_DETAILS가 포함되어 있으면 이미지가 아닌 에러 박스 표시
                if "ERROR_DETAILS" in item['path']:
                    error_message = item['path'].replace("ERROR_DETAILS:", "").strip()
                    st.warning(f"⚠️ **이미지 생성 실패**\n\n{error_message}")
                else:
                    try: 
                        if TARGET_RATIO == "16:9":
                            st.image(item['path'], use_container_width=True)
                        else:
                            sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1]) 
                            with sub_c2:
                                st.image(item['path'], use_container_width=True)
                    except: 
                        st.error("이미지 파일 로드 실패")
                
                # [NEW] 이미지 개별 재생성 버튼
                if st.button(f"🔄 이 장면만 이미지 다시 생성", key=f"regen_img_{index}", use_container_width=True):
                    if not api_key:
                        st.error("API Key가 필요합니다.")
                    else:
                        with st.spinner(f"Scene {item['scene']} 다시 그리는 중..."):
                            client = genai.Client(api_key=api_key)
                            
                            # 1. 프롬프트 다시 생성
                            current_title = st.session_state.get('video_title', '')
                            _, new_prompt = generate_prompt(
                                api_key, index, item['script'], style_instruction, 
                                current_title, SELECTED_GENRE_MODE,
                                target_language,
                                LAYOUT_KOREAN
                            )

                            # [추가] 재생성 시에도 프롬프트 에러 체크
                            if "API_ERROR" in new_prompt:
                                st.error(new_prompt) # 에러 메시지 출력
                            else:
                                # 2. 이미지 생성
                                new_path = generate_image(
                                    client, new_prompt, item['filename'], 
                                    IMAGE_OUTPUT_DIR, SELECTED_IMAGE_MODEL,
                                    TARGET_RATIO 
                                )
                                
                                if new_path and "ERROR_DETAILS" not in new_path:
                                    st.session_state['generated_results'][index]['path'] = new_path
                                    st.session_state['generated_results'][index]['prompt'] = new_prompt
                                    st.success("이미지가 변경되었습니다!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    err_msg = new_path.replace("ERROR_DETAILS:", "") if new_path else "Unknown Error"
                                    st.error(f"이미지 생성 실패: {err_msg}")

            # [오른쪽] 정보
            with cols[1]:
                st.subheader(f"Scene {item['scene']:02d}")
                st.caption(f"파일명: {item['filename']}")
                st.write(f"**대본:** {item['script']}")
                
                st.markdown("---")

                with st.expander("프롬프트 확인"):
                    st.text(item['prompt'])
                try:
                    # 에러가 아닐 때만 다운로드 버튼 활성화
                    if "ERROR_DETAILS" not in item['path']:
                        with open(item['path'], "rb") as file:
                            st.download_button("⬇️ 이미지 저장", data=file, file_name=item['filename'], mime="image/png", key=f"btn_down_{item['scene']}")
                except: pass

