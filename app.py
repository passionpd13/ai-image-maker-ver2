import streamlit as st
import requests
import random
import json
import time
import os
import re
import shutil
import zipfile
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

# 파일 저장 경로 설정
BASE_PATH = "./web_result_files"
IMAGE_OUTPUT_DIR = os.path.join(BASE_PATH, "output_images")

# 텍스트 모델 설정
GEMINI_TEXT_MODEL_NAME = "gemini-2.5-pro" 

# ==========================================
# [함수] 1. 유틸리티 함수
# ==========================================
def init_folders():
    # 동영상 폴더 생성 로직 제거
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
# [함수] 2. 프롬프트 생성 (원본 로직 유지)
# ==========================================
def generate_prompt(api_key, index, text_chunk, style_instruction, video_title, genre_mode="info", target_language="Korean", target_layout="16:9 와이드 비율"):
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

    # [9:16 강력 보정 로직]
    vertical_force_prompt = ""
    if "9:16" in target_layout:
        vertical_force_prompt = """
    [❗❗ 9:16 세로 화면 필수 지침 (Vertical Mode) ❗❗]
    1. **구도(Composition):** 가로로 넓은 풍경(Landscape)을 절대 그리지 마십시오.
    2. **배치(Placement):** 피사체는 화면 중앙에 수직으로 배치되어야 합니다. (위아래로 길게)
    3. **치타/동물 예시:** 동물이 달리는 장면이라면, 옆모습(Side view) 대신 **정면에서 달려오는 모습(Front view)**을 구도를 사용하여 세로 화면을 채우십시오.
        """

    # 공통 헤더
    common_header = f"""
    [화면 구도 지침]
    {target_layout}
    {vertical_force_prompt}
    """

    # ---------------------------------------------------------
    # 모드별 프롬프트 로직
    # ---------------------------------------------------------
    if genre_mode == "info":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 복잡한 상황을 아주 쉽고 직관적인 그림으로 표현하는 '비주얼 커뮤니케이션 전문가'이자 '교육용 일러스트레이터'입니다.

    [전체 영상 주제] "{video_title}"
    [그림 스타일 가이드] {style_instruction}
    
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
    9. 배경 현실감(Background Realism): 배경은 단순한 평면이 아닌, **깊이감(Depth)**과 **질감(Texture)**이 살아있는 입체적인 공간으로 연출하십시오.

    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 이미지 생성 AI가 그릴 수 있는 **구체적인 묘사 프롬프트**를 작성하십시오.
    
    [작성 요구사항]
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **세로 모드 시:** 캐릭터나 사물이 작아 보이지 않게 줌인(Zoom-in)하여 묘사하십시오.
    - **포함 요소:** 캐릭터 행동, 배경, 시각적 은유.
    
    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가적인 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

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
    - **실사 사진, 3D 렌더링, 사람 피부 질감 절대 금지.**
    - 무조건 **'그림(Illustration/Drawing/Manhwa)'** 느낌이 나야 합니다.

    [핵심 비주얼 스타일 가이드]
    1. **캐릭터:** 얼굴이 둥근 하얀색 스틱맨. 선은 굵고 부드러우며 그림자가 들어가 입체감이 느껴져야 함.
    2. **배경:** 단순한 단색 배경 금지. 고해상도 컨셉 아트 수준으로 배경 묘사.
    3. **조명:** 2D지만 입체적인 조명과 그림자 사용.
    4. **연기:** 캐릭터가 행동(Action)하는 장면 포착. 감정은 몸짓으로 전달.
    5. **언어:** {lang_guide} {lang_example}
    6. **구도:** {target_layout} 꽉 찬 구도.

    [임무]
    제공된 대본 조각을 읽고, 한 장면의 영화 스틸컷 같은 프롬프트를 작성하십시오.
    - **분량:** 최소 7문장 이상으로 상세하게 묘사.
    - **무조건 한국어(한글)**로만 작성하십시오.
        """

    elif genre_mode == "history":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **세계사의 결정적인 순간들**을 전달하는 '시대극 애니메이션 감독'입니다.
    역사적 비극을 다루지만, 절대로 잔인하거나 혐오스럽거나 고어틱하게 묘사를 하지 않습니다.

    [전체 영상 주제] "{video_title}"
    [그림 스타일 가이드] {style_instruction}
    
    [필수 연출 지침]
    1. **매체:** 무조건 **평면적인 '2D 스틱맨 일러스트레이션'** 스타일. (3D, 실사 금지)
    2. **텍스트 현지화:** {lang_guide} {lang_example}
    3. **비극의 상징화:** 전쟁, 죽음은 직접 묘사 대신 남겨진 물건, 그림자 등으로 간접 표현.
    4. **캐릭터 연기:** 과장된 표정보다는 '몸짓'과 '분위기'로 감정 표현.
    5. **색감:** 차분하고 애상적인 색감 사용.
    6. **구성:** {target_layout}. 분할 화면 금지.
    
    [임무]
    제공된 대본 조각을 바탕으로, 구체적인 묘사 프롬프트를 작성하십시오.
    - **분량:** 최소 7문장 이상.
    - **무조건 한국어**로만 작성하십시오.
    - 프롬프트에 '얼굴이 둥근 2d 스틱맨' 무조건 포함.
        """

    elif genre_mode == "3d_docu":
        vertical_zoom_guide = ""
        if "9:16" in target_layout:
            vertical_zoom_guide = """
    5. **[9:16 세로 모드 필수 지침 - 인물 확대]:**
        - 스마트폰 화면 특성상 인물이 멀리 있으면 시인성이 떨어집니다.
        - **카메라를 피사체(마네킹) 가까이 배치하여, 머리와 상반신이 화면의 50% 이상을 차지하도록 꽉 차게 연출하십시오.**
            """

        full_instruction = f"""
    {common_header}
    [역할]
    당신은 'Unreal Engine 5'를 사용하는 3D 시네마틱 아티스트입니다.
    현대 사회의 이슈나 미스터리한 현상을 고퀄리티 3D 그래픽으로 시각화합니다.

    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [핵심 비주얼 스타일 가이드]
    1. **화풍:** "A realistic 3D game cinematic screenshot", "Unreal Engine 5 render style".
    2. **캐릭터:** 매끈하고 하얀, 이목구비가 없는 마네킹 머리. 눈코입 없음. 현실적인 의상 착용.
    3. **조명 및 분위기:** 다소 어둡고, 미스터리하며, 진지한 분위기.
    4. **언어:** {lang_guide} {lang_example}
    {vertical_zoom_guide}

    [임무]
    위 스타일이 적용된 이미지 생성 프롬프트를 작성하십시오.
    - 프롬프트 시작에 **"언리얼 엔진 5 스타일, Realistic 3D game screenshot, Smooth white featureless mannequin head character"** 포함.
    - **무조건 한국어(한글)**로만 작성하십시오.
        """
        
    elif genre_mode == "scifi":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 'Fern', 'AiTelly' 스타일의 **깔끔하고 명확한 '3D 테크니컬 애니메이터'**입니다.
    복잡한 기계나 과학 원리를 설명하되, **엔지니어/과학자 캐릭터의 행동**을 통해 시청자의 이해를 돕습니다.

    [전체 영상 주제] "{video_title}"
    [유저 스타일 선호] {style_instruction}

    [핵심 비주얼 스타일 가이드]
    1. **화풍:** "3D Technical Animation", "Blender Cycles Render", "Clean rendering".
    2. **분위기:** 깔끔하고 밝은 스튜디오 조명.
    3. **피사체:** 기계의 단면도(Cutaway), 투시도 활용. 엔지니어/과학자 3D 캐릭터 등장.
    4. **언어:** {lang_guide} {lang_example}

    [임무]
    공학 교육 영상의 한 장면 같은 3D 프롬프트를 작성하십시오.
    - 시작 부분에 **"3D technical animation, Blender Cycles render, Clean studio lighting, Cutaway view"** 포함.
    - **무조건 한국어(한글)**로만 작성하십시오.
        """

    elif genre_mode == "paint_explainer":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 유튜브 'The Paint Explainer' 채널 스타일의 **'깔끔하고 직관적인 스틱맨 디지털 일러스트레이터'**입니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [필수 연출 지침]
    1. **배경:** 단순화된 2D 플랫 배경 (Simple 2D Flat Background). 하얀 여백 금지.
    2. **작화:** 깔끔하고 매끄러운 선(Clean & Smooth Lines). 명암 없는 평면 스타일.
    3. **캐릭터:** 하얀색 얼굴이 둥근 스틱맨. 굵은 검은색 외곽선. 역동적인 포즈.
    4. **소품 및 은유:** 핵심 사물을 아이콘처럼 단순화. 만화적 기호(땀방울, 느낌표 등) 적극 활용.
    5. **색상:** 밝고 선명한 플랫 컬러.
    6. **텍스트:** {lang_guide} {lang_example}. 굵고 다양한 손글씨 느낌.

    [임무]
    '깔끔한 The Paint Explainer 스타일'의 프롬프트를 작성하십시오.
    - 필수 키워드: "Clean digital line art, smooth lines, minimal vector style, flat design aesthetic"
    - **한글**로만 출력하십시오.
        """

    elif genre_mode == "comic_realism":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **'고퀄리티 실사 배경에 우스꽝스러운 합성을 하는 초현실주의 아티스트'**입니다.
    내셔널 지오그래픽 다큐멘터리에 '병맛' 스티커를 붙인 듯한 이미지를 만듭니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [핵심 비주얼 스타일 가이드]
    1. **베이스:** 극도로 사실적인 실사 (Unreal Engine 5, 8K Photo).
    2. **반전 포인트 1 (사람):** 몸은 실사, 얼굴은 **'릭 앤 모티' 스타일 2D 카툰** (단순한 눈, 점 눈동자).
    3. **반전 포인트 2 (동물):** 털/몸은 실사, 눈은 **'단순한 2D 만화 눈'** (흰자위+검은 점).
    4. **조명:** 웅장하고 진지하게 연출하여 우스꽝스러운 얼굴과 대비 극대화.
    5. **텍스트:** {lang_guide} {lang_example}. 거의 연출하지 않음.

    [임무]
    위 스타일이 적용된 프롬프트를 작성하십시오.
    - 필수 키워드: "Photorealistic 8k render, Funny 2D cartoon face on realistic body, Visual comedy"
    - **한글**로만 작성하십시오.
        """

    elif genre_mode == "pink_skull":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **'Helix' 채널 스타일의 3D 아티스트**입니다.
    기괴하지만 유머러스한 **'투명한 플라스틱/유리 재질의 해골'**이 등장합니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [핵심 비주얼 스타일 가이드]
    1. **배경:** 무조건 **'단색 핑크 배경 (Solid Pink Background)'**.
    2. **캐릭터:** 투명 플라스틱 해골. 내부 뼈대 보임. **선명한 하얀 눈알** 필수.
    3. **자세:** 소파나 의자에 앉아있는 구도 우선.
    4. **소품:** 대본 속 물건을 사실적으로 표현.
    5. **텍스트:** {lang_guide} {lang_example}.

    [임무]
    위 스타일이 적용된 프롬프트를 작성하십시오.
    - 필수 키워드: "3D render, Translucent clear plastic human skeleton, Funny Googly eyes, Solid Pink background"
    - **한글**로만 작성하십시오.
        """

    elif genre_mode == "webtoon":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 네이버 웹툰 스타일의 **'인기 웹툰 메인 작화가'**입니다.

    [전체 영상 주제] "{video_title}"
    [그림 스타일 가이드] {style_instruction}

    [필수 연출 지침]
    1. **작화:** 한국 웹툰 특유의 선명한 외곽선과 화려한 채색.
    2. **캐릭터:** 8등신 웹툰 주인공 스타일 (스틱맨 금지).
    3. **배경:** 캐릭터 주변 상황과 장소를 매우 구체적으로 묘사.
    4. **텍스트:** {lang_guide} {lang_example}. 말풍선 느낌이나 배경 오브젝트에 녹여냄.

    [임무]
    제공된 대본을 바탕으로 이미지 생성 프롬프트를 작성하십시오. (한글 출력)
    - "디테일한 사무실 배경을 뒤로 하고..." 처럼 공간 묘사 우선.
        """

    elif genre_mode == "manga":
        full_instruction = f"""
    {common_header}
    [역할]
    당신은 **작화 퀄리티가 극도로 높은 '대작 귀여운 지브리풍 애니메이션'의 총괄 작화 감독**입니다.

    [전체 영상 주제] "{video_title}"
    [스타일 가이드] {style_instruction}

    [필수 연출 지침]
    1. **작화:** 선명하고 정보량이 많은 고퀄리티 작화. 배경 디테일 집요하게 묘사.
    2. **행동:** 캐릭터의 행동과 표정을 역동적으로 순간 포착.
    3. **대본 충실도:** 대본의 지문을 하나도 놓치지 않고 시각화.
    4. **텍스트:** {lang_guide} {lang_example}

    [임무]
    최상급 귀여운 지브리풍 퀄리티의 애니메이션 프롬프트를 작성하십시오.
    - **한글**로만 출력하십시오.
        """

    else: # Fallback
        full_instruction = f"스타일: {style_instruction}. 비율: {target_layout}. 대본 내용: {text_chunk}. 이미지 프롬프트 작성."

    # 공통 실행 로직
    payload = {
        "contents": [{"parts": [{"text": f"Instruction:\n{full_instruction}\n\nScript Segment:\n\"{text_chunk}\"\n\nImage Prompt (Korean Only, Safe for Work):"}]}]
    }

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
            except:
                prompt = text_chunk
            return (scene_num, prompt)
        elif response.status_code == 429:
            time.sleep(2)
            return (scene_num, f"일러스트 묘사: {text_chunk}")
        else:
            return (scene_num, f"Error generating prompt: {response.status_code}")
    except Exception as e:
        return (scene_num, f"Error: {e}")

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
    # 동영상 재생 시간 관련 슬라이더 제거됨 (이미지 전용)
    
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

    PRESET_PAINT = """'The Paint Explainer' 유튜브 채널 스타일 (Expressive Clean Stickman).
화풍: '깔끔하고 매끄러운 디지털 선화(Clean Smooth Lines)'와 '굵은 손글씨(Bold Handwriting)' 텍스트.
배경: 흰색 여백 금지. 하늘, 땅, 벽, 바닥 등이 단순하게 면으로 구분된 '플랫한 2D 배경'.
캐릭터: 하얀색 얼굴이 둥근 2d 스틱맨. **핵심은 과장된 표정과 역동적인 행동으로 감정을 극적으로 연출하는 것.** 캐릭터가 크게 잘 보이게 배치.
채색: 명암 없는 '다채로운 플랫 컬러'를 사용하여 생동감 부여.
연출: 직관적인 사물 표현과 만화적 기호 적극 활용.
대본의 상황을 잘 나타내게 분활화면으로 말고 하나의 장면으로 연출."""

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
캐릭터의 표정과 행동을 '순간 포착'하듯 역동적으로 묘사.
대본의 지문을 하나도 놓치지 않고 시각화하는 '철저한 디테일' 위주. (16:9)
전체 대본에 어울리는 하나의 장면으로 연출."""

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

    def set_radio_to_custom():
        st.session_state.genre_radio_key = OPT_CUSTOM

    genre_select = st.radio(
        "콘텐츠 성격 선택:",
        (OPT_INFO, OPT_REALISTIC, OPT_HISTORY, OPT_3D, OPT_SCIFI, OPT_PAINT, OPT_COMIC_REAL, OPT_SKULL, OPT_WEBTOON, OPT_MANGA, OPT_CUSTOM),
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
        status_box.write(f"✂️ 대본 분할 중...")
        chunks = split_script_by_time(script_input, chars_per_chunk=100)
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
                    st.error(f"🚨 Scene {s_num} 실패!\n이유: {error_reason}")
                    st.caption(f"문제의 파일명: {fname}")

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
    
    # 동영상 관련 버튼 제거되고 ZIP 다운로드만 남음
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
                try: 
                    if TARGET_RATIO == "16:9":
                        st.image(item['path'], use_container_width=True)
                    else:
                        sub_c1, sub_c2, sub_c3 = st.columns([1, 2, 1]) 
                        with sub_c2:
                            st.image(item['path'], use_container_width=True)
                except: 
                    st.error("이미지 없음")
                
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

            # [오른쪽] 정보 (동영상 컨트롤 제거됨)
            with cols[1]:
                st.subheader(f"Scene {item['scene']:02d}")
                st.caption(f"파일명: {item['filename']}")
                st.write(f"**대본:** {item['script']}")
                
                st.markdown("---")
                # 동영상 생성/재생 관련 UI 제거됨

                with st.expander("프롬프트 확인"):
                    st.text(item['prompt'])
                try:
                    with open(item['path'], "rb") as file:
                        st.download_button("⬇️ 이미지 저장", data=file, file_name=item['filename'], mime="image/png", key=f"btn_down_{item['scene']}")
                except: pass
