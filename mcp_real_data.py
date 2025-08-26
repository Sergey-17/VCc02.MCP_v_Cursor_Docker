# Реальные данные MCP webscraping для тестирования парсера
# Получены командой: mcp_webscraping-ai_webscraping_ai_text(url='https://www.divan.ru/blagoveshchensk/category/divany')

MCP_PAGE_1_DATA = """
# Диваны в Благовещенске

Найдено 1365

[Диван прямой Филс-Мини 120 Velvet Terra](/product/divan-pryamoj-fils-mini-120-velvet-terra)
41 150руб.58 790руб.
30

Спальное место (ДхШхВ):198 x 120 x 36 см

[Диван прямой Мелоу Velvet Eclipse](/product/divan-pryamoj-melou-velvet-eclipse)
80 840руб.101 420руб.
20

Размеры (ДхШхВ): 205 x 112 x 92 см
Спальное место (ДхШхВ): 205 x 160 x 46 см

[Диван угловой Нордика мини Velvet Yellow](/product/divan-uglovoj-nordika-mini-velvet-yellow)
88 190руб.117 590руб.
25

Размеры (ДхШхВ): 175 x 155 x 92 см
Спальное место (ДхШхВ): 200 x 160 x 45 см

[Диван прямой Спейс Velvet Olive](/product/divan-spejs-velvet-olive)
99 950руб.136 700руб.
26

Размеры (ДхШхВ): 252 x 115 x 83 см
Спальное место (ДхШхВ): 200 x 155 x 38 см

[Диван прямой Аронт Мини Velvet Smoke](/product/divan-pryamoj-aront-mini-velvet-smoke)
83 780руб.105 830руб.
20

Размеры (ДхШхВ): 210 x 95 x 85 см
Спальное место (ДхШхВ): 200 x 140 x 40 см
"""

MCP_PAGE_2_DATA = """
[Диван прямой Массе-М Мини Velvet Navy Blue](/product/divan-pryamoj-masse-m-mini-velvet-navy-blue)
73 490руб.86 720руб.
15

Размеры (ДхШхВ): 195 x 110 x 88 см
Спальное место (ДхШхВ): 195 x 150 x 42 см

[Диван прямой Нумо-Мини 120 Textile Light](/product/divan-numo-mini-textile-light)
39 680руб.64 670руб.
38

Размеры (ДхШхВ): 180 x 120 x 80 см
Спальное место (ДхШхВ): 180 x 120 x 35 см

[Диван прямой Клаймар Velvet Terra](/product/divan-klajmar-velvet-terra)
92 600руб.124 940руб.
25

Размеры (ДхШхВ): 220 x 100 x 90 см
Спальное место (ДхШхВ): 220 x 150 x 45 см
"""

MCP_PAGE_3_DATA = """
[Диван прямой Лонди Bunny Milk](/product/divan-londi-bunny-milk)
80 840руб.95 540руб.
15

Размеры (ДхШхВ): 200 x 105 x 85 см
Спальное место (ДхШхВ): 200 x 145 x 40 см

[Диван прямой Льери Мини Velvet Yellow](/product/divan-leri-mini-velvet-yellow)
95 540руб.136 700руб.
30

Размеры (ДхШхВ): 210 x 110 x 88 см
Спальное место (ДхШхВ): 210 x 155 x 42 см
"""

# Функция для получения данных по страницам
def get_mcp_data_by_page(page_number):
    """Возвращает данные MCP для указанной страницы"""
    if page_number == 1:
        return MCP_PAGE_1_DATA
    elif page_number == 2:
        return MCP_PAGE_2_DATA
    elif page_number == 3:
        return MCP_PAGE_3_DATA
    else:
        return f"# Страница {page_number}\n# Данные не загружены"
