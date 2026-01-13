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
    page_title="열정피디 AI 이미지 생성기 VER.2",
    layout="wide",
    page_icon="🎨",
    initial_sidebar_state="expanded"
)

# 사용자별 고유 세션 ID 생성
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = str(uuid.uuid4())

# ==========================================
# [디자인] 다크모드 & 가독성 완벽 패치 (헤더/상태창/Expander)
# ==========================================
st.markdown("""
    <style>
    /* 1. 상단 헤더 (Deploy 버튼 있는 줄) 배경색 */
    header[data-testid="stHeader"] {
        background-color: #0E1117 !important;
        z-index: 1 !important;
    }

    /* 2. 콘텐츠 영역 상단 여백 대폭 확대 (겹침 방지) */
    .block-container {
        padding-top: 6rem !important; 
        padding-bottom: 5rem !important;
    }

    /* 3. 전체 배경 및 폰트 설정 */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF !important;
        font-family: 'Pretendard', sans-serif;
    }

    /* 텍스트 가독성 강화 (흰색 강제) */
    p, div, label, span, li, h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF !important;
    }
    
    /* 강조 텍스트 그림자 */
    h1, h2 {
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    /* 4. 배너 스타일 */
    .student-banner {
        background: linear-gradient(90deg, #6a11cb 0%, #2575fc 100%);
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

    /* 5. 입력창 라벨 스타일 */
    .stTextInput label p, .stTextArea label p, .stSelectbox label p, .stRadio label p {
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: #FFD700 !important; /* 금색 강조 */
        margin-bottom: 8px !important;
    }

    /* 입력창 내부 스타일 */
    .stTextInput input, .stTextArea textarea {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
        border: 1px solid #4A4A4A !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #2575fc !important;
        box-shadow: 0 0 8px rgba(37, 117, 252, 0.5);
    }

    /* 6. Selectbox (언어 선택창) 글씨 보이게 수정 */
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

    /* 다운로드 버튼 스타일 */
    [data-testid="stDownloadButton"] button {
        background-color: #2C2F38 !important;
        border: 1px solid #555 !important;
        color: white !important;
    }
    [data-testid="stDownloadButton"] button:hover {
        border-color: #00BFFF !important;
        color: #00BFFF !important;
    }

    /* [긴급 수정] 8. Expander (프롬프트 수정 & 확인) 스타일 완벽 고정 */
    /* Expander 컨테이너 */
    div[data-testid="stExpander"] details {
        background-color: #1F2128 !important;
        border: 1px solid #4A4A4A !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
    }

    /* 제목 줄 (Summary) - 마우스 뗐을 때(기본) */
    div[data-testid="stExpander"] details > summary {
        background-color: #1F2128 !important; /* 배경 어둡게 강제 */
        color: #FFFFFF !important;             /* 글씨 흰색 강제 */
    }

    /* 제목 줄 - 마우스 올렸을 때(Hover) */
    div[data-testid="stExpander"] details > summary:hover {
        background-color: #2C2F38 !important;
        color: #FFD700 !important;             /* 금색 */
    }

    /* 제목 줄 내부 텍스트 및 아이콘 */
    div[data-testid="stExpander"] details > summary span {
        color: inherit !important;
    }
    div[data-testid="stExpander"] details > summary svg {
        fill: #FFFFFF !important;
    }
    div[data-testid="stExpander"] details > summary:hover svg {
        fill: #FFD700 !important;
    }

    /* Expander 내부 콘텐츠 영역 배경 */
    div[data-testid="stExpander"] details > div {
        background-color: #1F2128 !important;
        color: #FFFFFF !important;
    }
    
    /* 9. Status Widget (작업 진행 중) 글씨 가독성 완벽 해결 */
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

    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #12141C;
        border-right: 1px solid #2C2F38;
    }
    </style>

    <div class="student-banner">
        🎨 열정피디 AI 이미지 생성기 VER.2
    </div>
""", unsafe_allow_html=True)

# 파일 저장 경로
BASE_PATH = "./web_result_files"

# ==========================================
# [함수] 1. 유틸리티 (대본 분할, 파일명 등)
# ==========================================
def split_script_by_time(script, chars_per_chunk=100):
    """
    대본을 문장 단위로 끊어서 적절한 길이로 병합하되,
    너무 짧은 문장(예: 인사말)이 혼자 덩그러니 남지 않도록 최소 길이를 보장합니다.
    """
    temp_sentences = script.replace(".", ".|").replace("?", "?|").replace("!", "!|").split("|")
    chunks = []
    current_chunk = ""
    
    # 최소 보장 글자 수
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
            # 기존 덩어리가 너무 짧으면 이번 문장까지 포함
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
    """파일 이름 생성 (특수문자 제거)"""
    clean_line = text_chunk.replace("\n", " ").strip()
    clean_line = re.sub(r'[\\/:*?"<>|]', "", clean_line)
    words = clean_line.split()
    if len(words) <= 6:
        summary = " ".join(words)
    else:
        summary = f"{' '.join(words[:3])}...{' '.join(words[-3:])}"
    return f"S{scene_num:03d}_{summary}.png"

def create_zip_buffer(source_dir):
    """폴더 압축"""
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                zip_file.write(file_path, os.path.basename(file_path))
    buffer.seek(0)
    return buffer

# ==========================================
# [함수] 2. 프롬프트 생성 (사용자 지정 코드 100% 준수)
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
    else:
        # [모드 1] 밝은 정보/이슈
        full_instruction = f"""
    [역할]
    당신은 복잡한 상황을 아주 쉽고 직관적인 그림으로 표현하는 '비주얼 커뮤니케이션 전문가'이자 '교육용 일러스트레이터'입니다.

    [전체 영상 주제]
    "{video_title}"

    [그림 스타일 가이드 - 절대 준수]
    {style_instruction}
    
    [필수 연출 지침]
    1. **조명(Lighting):** 무조건 **'밝고 화사한 조명(High Key Lighting)'**을 사용하십시오. 그림자가 짙거나 어두운 부분은 없어야 합니다.
    2. **색감(Colors):** 채도가 높고 선명한 색상을 사용하여 시인성을 높이십시오. (칙칙하거나 회색조 톤 금지)
    3. **구성(Composition):** 시청자가 상황을 한눈에 이해할 수 있도록 피사체를 화면 중앙에 명확하게 배치하십시오.
    4. **분위기(Mood):** 교육적이고, 중립적이며, 산뜻한 분위기여야 합니다. **(절대 우울하거나, 무섭거나, 기괴한 느낌 금지)**
    5. 분활화면으로 연출하지 말고 하나의 화면으로 연출한다.
    6. **[텍스트 언어]:** {lang_guide} {lang_example}
    - **[절대 금지]:** 화면의 네 모서리(Corners)나 가장자리(Edges)에 글자를 배치하지 마십시오. 글자는 반드시 중앙 피사체 주변에만 연출하십시오.
    7. 캐릭터의 감정도 느껴진다.

    [임무]
    제공된 대본 조각(Script Segment)을 바탕으로, 이미지 생성 AI가 그릴 수 있는 **구체적인 묘사 프롬프트**를 작성하십시오.
    
    [작성 요구사항]
    - **분량:** 최소 5문장 이상으로 상세하게 묘사.
    - **포함 요소:**
        - **캐릭터 행동:** 대본의 상황을 연기하는 캐릭터의 구체적인 동작.
        - **배경:** 상황을 설명하는 소품이나 장소 (배경은 깔끔하게).
        - **시각적 은유:** 추상적인 내용일 경우, 이를 설명할 수 있는 시각적 아이디어 (예: 돈이 날아가는 모습, 그래프가 하락하는 모습 등).
    
    [출력 형식]
    - **무조건 한국어(한글)**로만 작성하십시오.
    - 부가적인 설명 없이 **오직 프롬프트 텍스트만** 출력하십시오.
        """

    max_retries = 3
    target_models = ["gemini-3-pro-preview", "gemini-2.5-flash"]

    for attempt in range(1, max_retries + 1):
        for model_name in target_models:
            try:
                time.sleep(random.uniform(0.2, 0.5))
                
                # 안전 필터 설정은 유지
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
                error_msg = str(e)
                time.sleep(1)

    return (scene_num, f"주제 '{video_title}'에 어울리는 배경 일러스트. (Safety Fallback)")

# ==========================================
# [함수] 3. 이미지 생성
# ==========================================
def generate_image(client, prompt, filename, output_dir, selected_model_name, style_instruction):
    full_path = os.path.join(output_dir, filename)
    
    # 스타일 지침과 프롬프트 결합
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
    # 라벨을 보이지 않게 숨김 처리 (label_visibility="collapsed")
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

    if 'style_prompt_area' not in st.session_state:
        st.session_state['style_prompt_area'] = PRESET_INFO

    def update_style_text():
        selection = st.session_state.genre_radio
        if selection == "밝은 정보/이슈 (Bright & Flat)":
            st.session_state['style_prompt_area'] = PRESET_INFO
        else:
            st.session_state['style_prompt_area'] = PRESET_HISTORY

    # 라벨 숨김
    genre_select = st.radio(
        "장르 선택", 
        ("밝은 정보/이슈 (Bright & Flat)", "역사/다큐 (Cinematic & Immersive)"), 
        index=0,
        key="genre_radio",
        on_change=update_style_text,
        label_visibility="collapsed"
    )

    if "밝은 정보" in genre_select:
        SELECTED_GENRE_MODE = "info"
    else:
        SELECTED_GENRE_MODE = "history"

    st.markdown("---")

    # 3. 이미지 텍스트 언어 선택
    st.subheader("🌐 이미지 텍스트 언어")
    # 라벨 숨김
    target_language = st.selectbox(
        "이미지 텍스트 언어",
        ("Korean", "English", "Japanese"),
        index=0,
        label_visibility="collapsed"
    )

    st.markdown("---")

    st.subheader("🖌️ 그림체 지침 (수정 가능)")
    # 라벨 숨김
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
        status_box.write(f"📝 프롬프트 작성 중... (Mode: {genre_select}, Lang: {target_language})")
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
            
            # [오른쪽: 정보 및 수정] 먼저 선언하여 변수 확보
            with cols[1]:
                st.markdown(f"### Scene {item['scene']:02d}")
                st.markdown(f"**대본:**\n\n{item['script']}")
                
                with st.expander("📝 프롬프트 수정 & 확인", expanded=False):
                    # [NEW] 프롬프트를 수정할 수 있는 Text Area
                    # key를 index 기반으로 생성하여 각 장면별로 독립적 관리
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
                        # [핵심 로직 변경]
                        # 기존처럼 generate_prompt를 호출하는 것이 아니라,
                        # 위 text_area에서 사용자가 수정했을 수도 있는 'edited_prompt'를 가져옵니다.
                        # st.session_state[prompt_key]에 최신 값이 들어있습니다.
                        current_prompt_text = st.session_state.get(prompt_key, item['prompt'])

                        with st.spinner(f"Scene {item['scene']} 재생성 중..."):
                            client = genai.Client(api_key=api_key)
                            
                            # 수정된 프롬프트로 바로 이미지 생성 요청
                            new_path = generate_image(
                                client, 
                                current_prompt_text, 
                                item['filename'],
                                CURRENT_USER_DIR, 
                                SELECTED_IMAGE_MODEL, 
                                style_instruction
                            )
                            
                            if new_path:
                                # 결과 업데이트
                                st.session_state['generated_results'][index]['path'] = new_path
                                # 프롬프트도 최신 상태로 유지
                                st.session_state['generated_results'][index]['prompt'] = current_prompt_text
                                st.rerun()
                
                try:
                    with open(item['path'], "rb") as file:
                        st.download_button("⬇️ 이미지 저장", data=file, file_name=item['filename'], mime="image/png", key=f"btn_down_{item['scene']}")

                except: pass
