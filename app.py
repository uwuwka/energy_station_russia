import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
from supabase import create_client

st.set_page_config(
    page_title="Электростанции России",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

SUPABASE_URL = "https://xfcrnexxamqbewxffvns.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhmY3JuZXh4YW1xYmV3eGZmdm5zIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE1NzI1MzksImV4cCI6MjA3NzE0ODUzOX0.bU1dp2BtK_Nqs83n2NJtX8cMmOnNFGF2oUWHHTWUptI"

# Инициализация session state
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


def get_plant_icon(plant_type):
    icons = {'АЭС': '⚛️', 'ГЭС': '💧', 'ТЭЦ': '🔥'}
    colors = {'АЭС': 'red', 'ГЭС': 'blue', 'ТЭЦ': 'orange'}
    color = colors.get(plant_type, 'gray')
    icon = icons.get(plant_type, '🏭')
    return folium.DivIcon(
        html=f'<div style="font-size: 20px; color: {color};">{icon}</div>',
        icon_size=(20, 20), icon_anchor=(10, 10)
    )


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
                        power = plant.get(config['fields']['power']) or 0.1
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

    # Применение фильтров
    if filters['types']:
        filtered_df = filtered_df[filtered_df['Тип'].isin(filters['types'])]
    if filters['regions']:
        filtered_df = filtered_df[filtered_df['Регион'].isin(filters['regions'])]
    if filters['names']:
        filtered_df = filtered_df[filtered_df['Название'].isin(filters['names'])]
    if filters['owners']:
        filtered_df = filtered_df[filtered_df['Владелец'].isin(filters['owners'])]
    filtered_df = filtered_df[filtered_df['Мощность (МВт)'] >= filters['min_power']]

    if filters['sort_by']:
        filtered_df = filtered_df.sort_values(
            by=filters['sort_by'],
            ascending=filters['sort_ascending']
        )

    return filtered_df


def main():
    st.title("Карта электростанций России")
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
            'sort_by': None,
            'sort_ascending': True
        }

        if not st.session_state.df.empty:
            df = st.session_state.df

            filters['types'] = st.multiselect(
                "Тип станции:",
                options=sorted(df['Тип'].unique()),
                default=sorted(df['Тип'].unique())
            )

            filters['min_power'] = st.slider(
                "Минимальная мощность (МВт):",
                0, int(df['Мощность (МВт)'].max()), 0
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

            st.divider()
            st.header("📊 Сортировка")

            filters['sort_by'] = st.selectbox(
                "Сортировать по:",
                options=[None, 'Название', 'Тип', 'Регион', 'Мощность (МВт)', 'Владелец'],
                format_func=lambda x: 'Без сортировки' if x is None else x
            )

            if filters['sort_by']:
                filters['sort_ascending'] = st.radio(
                    "Порядок сортировки:",
                    ["По возрастанию", "По убыванию"],
                    horizontal=True
                ) == "По возрастанию"

        st.divider()
        st.header("Легенда")
        st.markdown("""
        - ⚛️ **АЭС** - Атомные электростанции
        - 💧 **ГЭС** - Гидроэлектростанции  
        - 🔥 **ТЭЦ** - Теплоэлектроцентрали
        """)

    if st.session_state.df.empty:
        st.info("👆 Нажмите кнопку 'Загрузить данные' в сайдбаре для начала работы")
        return

    filtered_df = apply_filters_and_sorting(st.session_state.df, filters)

    st.subheader("📈 Общая статистика")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Всего станций", len(filtered_df))
    with col2:
        st.metric("Общая мощность", f"{filtered_df['Мощность (МВт)'].sum():,.0f} МВт")
    with col3:
        st.metric("АЭС", len(filtered_df[filtered_df['Тип'] == 'АЭС']))
    with col4:
        st.metric("ГЭС", len(filtered_df[filtered_df['Тип'] == 'ГЭС']))
    with col5:
        st.metric("ТЭЦ", len(filtered_df[filtered_df['Тип'] == 'ТЭЦ']))

    if st.session_state.data_source == "demo":
        st.warning(
            "⚠️ Используются демо-данные. Для работы с реальными данными выберите 'База данных Supabase' в сайдбаре.")
    else:
        st.success(f"✅ Загружено {len(st.session_state.df)} станций из базы данных Supabase")

    st.subheader("🗺️ Интерактивная карта")
    st.markdown("Нажмите на маркер для получения подробной информации о станции")

    m = folium.Map(
        location=[64.6863136, 97.7453061],
        zoom_start=4,
        min_zoom=4,
    )
    for _, plant in filtered_df.iterrows():
        popup_text = f"""
        <div style="min-width: 280px; font-family: Arial, sans-serif;">
            <h3 style="color: #1f77b4; margin-bottom: 10px;">{plant['Название']}</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 4px;"><b>Тип:</b></td><td style="padding: 4px;">{plant['Тип']}</td></tr>
                <tr><td style="padding: 4px;"><b>Мощность:</b></td><td style="padding: 4px;">{plant['Мощность (МВт)']:,.0f} МВт</td></tr>
                <tr><td style="padding: 4px;"><b>Владелец:</b></td><td style="padding: 4px;">{plant['Владелец']}</td></tr>
                <tr><td style="padding: 4px;"><b>Регион:</b></td><td style="padding: 4px;">{plant['Регион']}</td></tr>
                <tr><td style="padding: 4px;"><b>Топливо:</b></td><td style="padding: 4px;">{plant['Топливо']}</td></tr>
            </table>
        </div>
        """

        folium.Marker(
            [plant['Широта'], plant['Долгота']],
            popup=folium.Popup(popup_text, max_width=350),
            tooltip=f"{plant['Название']} ({plant['Тип']}) - {plant['Мощность (МВт)']:,.0f} МВт",
            icon=get_plant_icon(plant['Тип'])
        ).add_to(m)

    st_folium(m, width=2000, height=1000, key="main_map")

    st.subheader("Информация о станциях")

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
                    "Мощность (МВт)": st.column_config.NumberColumn(format="%d"),
                    "Широта": st.column_config.NumberColumn(format="%.6f"),
                    "Долгота": st.column_config.NumberColumn(format="%.6f")
                }
            )
    else:
        st.info("Нет станций, соответствующих выбранным фильтрам")


if __name__ == "__main__":
    main()