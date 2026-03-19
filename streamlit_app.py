import streamlit as st
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv
import streamlit.components.v1 as components

load_dotenv()

st.set_page_config(
    page_title="Электростанции России",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
YANDEX_APIKEY = os.getenv("YANDEX_KEY")

icons = {'АЭС': '⚛️', 'ГЭС': '💧', 'ТЭЦ': '🔥'}

if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame()
if 'data_source' not in st.session_state:
    st.session_state.data_source = "demo"


def parse_coordinates(coord_text):
    if not coord_text or pd.isna(coord_text):
        return None, None
    try:
        coord_text = str(coord_text).replace(',', ' ')
        parts = [part.strip() for part in coord_text.split() if part.strip()]
        if len(parts) >= 2:
            return float(parts[0]), float(parts[1])
    except (ValueError, TypeError):
        pass
    return None, None


@st.cache_data(ttl=3600)
def load_supabase_data():
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        all_plants = []

        tables_config = [
            {
                'name': 'atomic_station',
                'type': 'АЭС',
                'fields': {
                    'name': 'название',
                    'power': 'мощность МВт',
                    'region': 'область',
                    'owner': 'собственник',
                    'coords': 'Координаты (широта  долгота)',
                    'fuel': 'Ядерное топливо'
                }
            },
            {
                'name': 'hydro_station',
                'type': 'ГЭС',
                'fields': {
                    'name': 'Название ГЭС',
                    'power': 'Мощность (МВт)',
                    'region': 'Субъект РФ',
                    'owner': 'собственник',
                    'coords': 'Координаты (широта долгота)',
                    'fuel': 'Вода'
                }
            },
            {
                'name': 'thermal_station',
                'type': 'ТЭЦ',
                'fields': {
                    'name': 'название',
                    'power': 'мощность МВт',
                    'region': 'область',
                    'owner': 'собственник',
                    'coords': 'Координаты (широта долгота)',
                    'fuel': 'основное топливо'
                }
            }
        ]

        for config in tables_config:
            try:
                response = supabase.table(config['name']).select("*").execute()
                if response.data:
                    for plant in response.data:
                        name = plant.get(config['fields']['name']) or 'Неизвестно'
                        power = plant.get(config['fields']['power']) or 1
                        region = plant.get(config['fields']['region']) or 'Неизвестно'
                        owner = plant.get(config['fields']['owner']) or 'Неизвестно'
                        fuel = plant.get(config['fields'].get('fuel', '')) or config['fields'].get('fuel', 'Неизвестно')
                        coordination = plant.get(config['fields']['coords']) or ""

                        lat, lon = parse_coordinates(coordination)
                        if lat is None or lon is None:
                            continue

                        all_plants.append({
                            'Название': name,
                            'Тип': config['type'],
                            'Регион': region,
                            'Мощность (МВт)': power,
                            'Владелец': owner,
                            'Топливо': fuel,
                            'Широта': lat,
                            'Долгота': lon
                        })
            except Exception as e:
                st.error(f"Ошибка загрузки {config['name']}: {e}")

        if all_plants:
            return pd.DataFrame(all_plants), "supabase"
        else:
            st.warning("Не удалось загрузить данные из базы. Используются демо-данные.")
            return pd.DataFrame(), "demo"
    except Exception as e:
        st.error(f"Ошибка подключения к Supabase: {e}")
        return pd.DataFrame(), "demo"


def get_demo_data():
    return pd.DataFrame([
        {'Название': 'Саяно-Шушенская ГЭС', 'Тип': 'ГЭС', 'Регион': 'Хакасия',
         'Мощность (МВт)': 6400, 'Владелец': 'РусГидро', 'Топливо': 'Вода',
         'Широта': 52.8294, 'Долгота': 91.3704},
        {'Название': 'Ленинградская АЭС', 'Тип': 'АЭС', 'Регион': 'Ленинградская область',
         'Мощность (МВт)': 4200, 'Владелец': 'Росатом', 'Топливо': 'Ядерное топливо',
         'Широта': 59.8370, 'Долгота': 29.0862},
        {'Название': 'Калининская АЭС', 'Тип': 'АЭС', 'Регион': 'Тверская область',
         'Мощность (МВт)': 4000, 'Владелец': 'Росатом', 'Топливо': 'Ядерное топливо',
         'Широта': 57.9109, 'Долгота': 35.0636},
        {'Название': 'Братская ГЭС', 'Тип': 'ГЭС', 'Регион': 'Иркутская область',
         'Мощность (МВт)': 4500, 'Владелец': 'РусГидро', 'Топливо': 'Вода',
         'Широта': 56.2864, 'Долгота': 101.7726},
        {'Название': 'Московская ТЭЦ-21', 'Тип': 'ТЭЦ', 'Регион': 'Москва',
         'Мощность (МВт)': 1800, 'Владелец': 'Мосэнерго', 'Топливо': 'Природный газ',
         'Широта': 55.7558, 'Долгота': 37.6176},
        {'Название': 'Сургутская ГРЭС-1', 'Тип': 'ТЭЦ', 'Регион': 'Ханты-Мансийский АО',
         'Мощность (МВт)': 3300, 'Владелец': 'Юнипро', 'Топливо': 'Природный газ',
         'Широта': 61.2540, 'Долгота': 73.3960}
    ])


def apply_filters_and_sorting(df, filters):
    filtered_df = df.copy()

    if filters['types']:
        filtered_df = filtered_df[filtered_df['Тип'].isin(filters['types'])]
    if filters['regions']:
        filtered_df = filtered_df[filtered_df['Регион'].isin(filters['regions'])]
    if filters['names']:
        filtered_df = filtered_df[filtered_df['Название'].isin(filters['names'])]
    if filters['owners']:
        filtered_df = filtered_df[filtered_df['Владелец'].isin(filters['owners'])]
    filtered_df = filtered_df[(filtered_df['Мощность (МВт)'] >= filters['min_power']) &
                              (filtered_df['Мощность (МВт)'] <= filters['max_power'])]

    return filtered_df


def create_yandex_map(df, api_key):
    plants_json = df.to_json(orient='records', force_ascii=False)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://api-maps.yandex.ru/2.1/?apikey={api_key}&lang=ru_RU" type="text/javascript"></script>
        <script type="text/javascript">
            ymaps.ready(init);

            function init() {{
                var myMap = new ymaps.Map("map", {{
                    center: [64.5, 97.0],
                    zoom: 4,
                    controls: ['zoomControl']
                }});

                var plants = {plants_json};
                console.log("Загружено станций:", plants.length);
                if (plants.length > 0) {{
                    console.log("Первая станция:", plants[0]);
                }}

                var colors = {{
                    'АЭС': 'red',
                    'ГЭС': 'blue',
                    'ТЭЦ': 'orange'
                }};

                var symbols = {{
                    'АЭС': '⚛️',
                    'ГЭС': '💧',
                    'ТЭЦ': '🔥'
                }};

                for (var i = 0; i < plants.length; i++) {{
                    var p = plants[i];
                    var color = colors[p['Тип']] || 'gray';
                    var symbol = symbols[p['Тип']] || '•';

                    var balloonContent = '<b>' + p['Название'] + '</b><br>' +
                                         'Тип: ' + p['Тип'] + '<br>' +
                                         'Мощность: ' + p['Мощность (МВт)'] + ' МВт<br>' +
                                         'Владелец: ' + p['Владелец'] + '<br>' +
                                         'Регион: ' + p['Регион'] + '<br>' +
                                         'Топливо: ' + p['Топливо'];

                    var svg = '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">' +
                              '<text x="60" y="62" font-size="50" text-anchor="middle" fill="white" font-family="Arial, sans-serif">' + symbol + '</text>' +
                              '</svg>';
                    var svgData = 'data:image/svg+xml,' + encodeURIComponent(svg);

                    var placemark = new ymaps.Placemark(
                        [p['Широта'], p['Долгота']],
                        {{ balloonContent: balloonContent }},
                        {{
                            iconLayout: 'default#image',
                            iconImageHref: svgData,
                            iconImageSize: [40, 40],
                            iconImageOffset: [-20, -20]
                        }}
                    );

                    myMap.geoObjects.add(placemark);
                }}
            }}
        </script>
    </head>
    <body>
        <div id="map" style="width: 100%; height: 600px;"></div>
    </body>
    </html>
    """
    return html


def main():
    st.title("⚡ Карта электростанций России")
    st.markdown("Интерактивная карта АЭС, ГЭС и ТЭС Российской Федерации")

    with st.sidebar:
        st.header("⚙️ Управление")

        data_source = st.radio(
            "Источник данных:",
            ["Демо-данные", "База данных Supabase"],
            index=0 if st.session_state.data_source == "demo" else 1
        )

        if st.button("🔄 Загрузить данные", use_container_width=True):
            if data_source == "База данных Supabase":
                with st.spinner("Загрузка данных из базы..."):
                    df, source = load_supabase_data()
                    st.session_state.df = df
                    st.session_state.data_source = source
            else:
                st.session_state.df = get_demo_data()
                st.session_state.data_source = "demo"
                st.success("✅ Загружены демо-данные")

        st.divider()
        st.header("🔍 Фильтры")

        filters = {
            'types': [],
            'regions': [],
            'names': [],
            'owners': [],
            'min_power': 0,
            'max_power': 0,
        }

        if not st.session_state.df.empty:
            df = st.session_state.df

            filters['types'] = st.multiselect(
                "Тип станции:",
                options=sorted(df['Тип'].unique()),
                default=sorted(df['Тип'].unique())
            )

            min_power_val = int(df['Мощность (МВт)'].min())
            max_power_val = int(df['Мощность (МВт)'].max())
            col1, col2 = st.columns(2)
            with col1:
                filters['min_power'] = st.number_input(
                    "Мин. мощность (МВт):",
                    min_value=0,
                    max_value=max_power_val,
                    value=min_power_val
                )
            with col2:
                filters['max_power'] = st.number_input(
                    "Макс. мощность (МВт):",
                    min_value=0,
                    max_value=max_power_val,
                    value=max_power_val
                )

            filters['regions'] = st.multiselect(
                "Регион:",
                options=sorted(df['Регион'].unique()),
                default=[]
            )

            filters['names'] = st.multiselect(
                "Название станции:",
                options=sorted(df['Название'].unique()),
                default=[]
            )

            filters['owners'] = st.multiselect(
                "Владелец:",
                options=sorted(df['Владелец'].unique()),
                default=[]
            )

    if st.session_state.df.empty:
        st.info("👆 Нажмите кнопку 'Загрузить данные' в сайдбаре для начала работы")
        return

    filtered_df = apply_filters_and_sorting(st.session_state.df, filters)

    st.subheader("📈 Общая статистика")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Всего станций", len(filtered_df))
    with col2:
        total_power = filtered_df['Мощность (МВт)'].sum()
        st.metric("Общая мощность", f"{total_power:,.0f} МВт")
    with col3:
        st.metric(f"АЭС {icons['АЭС']}", len(filtered_df[filtered_df['Тип'] == 'АЭС']))
    with col4:
        st.metric(f"ГЭС {icons['ГЭС']}", len(filtered_df[filtered_df['Тип'] == 'ГЭС']))
    with col5:
        st.metric(f"ТЭЦ {icons['ТЭЦ']}", len(filtered_df[filtered_df['Тип'] == 'ТЭЦ']))

    if st.session_state.data_source == "demo":
        st.warning(
            "⚠️ Используются демо-данные. Для работы с реальными данными выберите 'База данных Supabase' в сайдбаре.")
    else:
        st.success(f"✅ Загружено {len(st.session_state.df)} станций из базы данных Supabase")

    st.subheader("🗺️ Интерактивная карта")
    st.markdown("Нажмите на маркер для получения подробной информации о станции")

    if not filtered_df.empty:
        if YANDEX_APIKEY:
            map_html = create_yandex_map(filtered_df, YANDEX_APIKEY)
            components.html(map_html, height=620)
        else:
            st.error(
                "❌ Не указан API-ключ Яндекс.Карт. Добавьте его в файл .env как YANDEX_MAPS_APIKEY или прямо в код.")
    else:
        st.info("Нет станций, соответствующих выбранным фильтрам")

    st.subheader("📋 Информация о станциях")

    if not filtered_df.empty:
        columns_to_show = st.multiselect(
            "Выберите колонки для отображения:",
            options=['Название', 'Тип', 'Мощность (МВт)', 'Владелец', 'Регион', 'Топливо', 'Широта', 'Долгота'],
            default=['Название', 'Тип', 'Мощность (МВт)', 'Владелец', 'Регион']
        )

        if columns_to_show:
            st.dataframe(
                filtered_df[columns_to_show],
                use_container_width=True,
                height=400,
                column_config={
                    "Мощность (МВт)": st.column_config.NumberColumn(format="%.1f МВт"),
                    "Широта": st.column_config.NumberColumn(format="%.4f"),
                    "Долгота": st.column_config.NumberColumn(format="%.4f")
                }
            )
    else:
        st.info("Нет станций, соответствующих выбранным фильтрам")


if __name__ == "__main__":
    main()
