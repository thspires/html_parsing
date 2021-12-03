'''
- Le multiplos arquivos e retorna um html sumarizando os dados de busca por patentes do INPI
- Uso: python3 SOLUTION.py no diretorio que contem arquivos HTML obtidos de buscas no INPI
- O arquivo gerado (PATENTES.html) sera encontrado no subdiretorio PATENTES_HTML/
- A solução não gera arquivos em "3rd normal form,uma vez que a saída desejada era apenas um arquivo html. Repetições de dados em colunas são incluídas.
- PATENTES.html possui uma coluna chamada "Aviso" que alerta sobre a existencia de CNPJ/CPFs com mais patentes do que incluidas em arquivo individual
- Uma stylesheet (CSS) foi incluído dentro HTML para manter apenas um arquivo como saída.
- Para maiores volumes de dados talvez fosse util ter uma barra de busca no HTML. O pacote DT (do R) faz isso de uma maneira simples. 
  Essa solução foi incorporada, mas de maneira opcional: 
    modifique a variável global INCLUIR_DT para True. Se R estiver instalado e o script 'createDT.r' estiver diponivel no mesmo diretorio,
    o programa deverá retornar, de forma adicional, um arquivo chamado patentes_DT.html em formato DT padrao
    - Sera gerado um arquivo .csv que serve de passo intermediario para integracao com R
    - O arquivo nao eh apagado automaticamente
'''

import glob
import os
import re
import lxml
import numpy as np
import pandas as pd
import subprocess
from bs4 import BeautifulSoup

# Mofique para True para que chame script do R createDT.r, que ira criar um DataTable
INCLUIR_DT = False

def main():
  '''Creates and populates a DataFrame with info from patents html files. Calls functions for html file validation, and writes a HTML at ./PATENTES_HTML subdirectory'''
  # Criar boiler plate para o DataFrame
  tabela = pd.DataFrame(columns=['Arquivo','CNPJ','Resultado','No_pedido','Deposito','Titulo','IPC','Aviso'])
  files = glob.glob('*.html')
  assert files != [], "Diretorio atual nao contem arquivos HTML. Favor executar o programa no diretorio que contem os arquivos HTML de patentes para serem processados."
  
  for file in files:
    with open(file, 'r', encoding='latin-1') as html_file:
      content = html_file.read()
      soup = BeautifulSoup(content, 'lxml') #  melhor que o html_parser do bs4
      cnpj = get_cnpj_or_cpf(soup) # Ver helper function abaixo
      # Ha pedido de patente para este CPF ou CNPJ?
      pedidos = re.search('Pedido', soup.text)
      if pedidos == None:
        # Se nao ha pedido de patente, popular DataFrame com informacoes basicas
        d = {'Arquivo': [file], 'CNPJ': [cnpj], 'Resultado': [0], 'No_pedido': [np.NaN], 'Deposito':[np.NaN], 'Titulo':[np.NaN], 'IPC':[np.NaN], 'Aviso':[np.NaN]}
        resultado = pd.DataFrame(data = d)
        tabela = tabela.append(resultado)
      else:
        # Havendo pedidos, transformar a <table> do html em DataFrame e o popular com dados
        html_table = soup.find('table')
        html_table = html_table.prettify()
        parsed_table = pd.read_html(html_table)[0]
        parsed_table = parsed_table.iloc[9:] # Removendo HTML sem informacao util
        parsed_table.reset_index(inplace = True)
        parsed_table.drop(['index', 4], axis = 1, inplace = True)
        mask = (~parsed_table[0].str.contains('de Resultado')) # Booleano isolando a linha final da tabela
        parsed_table = parsed_table[mask] # Tabela sem a linha final
        parsed_table.columns = ['No_pedido', 'Deposito', 'Titulo', 'IPC']
        parsed_table['Arquivo'] = file
        parsed_table['CNPJ'] = cnpj
        resultado = parsed_table.shape[0]
        parsed_table['Resultado'] = resultado
        if resultado >= 20:
          parsed_table['Aviso'] = "Ha mais registros de patente para este CNPJ ou CPF!"
        tabela = tabela.append(parsed_table)
  tabela.fillna('-', inplace=True) # Padronizando NAs
  tabela.replace('-', '', inplace=True)
  
  # Create new directory to store html file(s)
  if not os.path.exists('./PATENTES_HTML/'):
    os.mkdir('./PATENTES_HTML/')
  
  # Criar DT se quiser
  if INCLUIR_DT == True: 
    create_DT_html(tabela)
  # Iniciar criacao do html padrao
  create_html_file(tabela)

# =======================#
# Begin helper functions #
# =======================#
def is_valid_html(soup):
  '''Search for the string - CPF ou CNPJ do Depositante word Depositante - abort execution if none '''
  depositante_string = re.search('CPF ou CNPJ do Depositante:', soup.text)
  if depositante_string == None:
    print('html invalido:' + file + '. Por favor, mantenha no diretorio apenas arquivos html de patentes')
    raise Exception("HTML provavelmente nao se refere a base de dados de patente")

def get_cnpj_or_cpf(soup):
  '''Pega um buffer depois da palavra Depositante e remover char nao numericos'''
  is_valid_html(soup)
  depositante = re.search('Depositante:', soup.text)
  initial_string_position = depositante.span()[1] + 1
  final_string_position = depositante.span()[1] + 20
  cnpj = soup.text[initial_string_position : final_string_position]
  cnpj = re.sub('[^0-9]', '', cnpj) # remover tudo que nao for numero
  return cnpj

def create_html_file(tabela):
  '''Adiciona CSS stylesheet e cria o arquivo html'''
  # Criar diretorio para salvar o arquivo
  os.chdir('./PATENTES_HTML/')    
  # Styling HTML file with CSS (stylesheet credit: https://dev.to/dcodeyt/creating-beautiful-html-tables-with-css-428l)
  header = "<body>\n<html>\n"
  style = "\n<style>\n.styled-table {\n    border-collapse: collapse;\n    margin: 25px 0;\n    font-size: 0.9em;\n    font-family: sans-serif;\n    min-width: 400px;\n    box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);\n}\n.styled-table thead tr {\n    background-color: #009879;\n    color: #ffffff;\n    text-align: left;\n}\n.styled-table th,\n.styled-table td {\n    padding: 12px 15px;\n}\n.styled-table tbody tr {\n    border-bottom: 1px solid #dddddd;\n}\n\n.styled-table tbody tr:nth-of-type(even) {\n    background-color: #f3f3f3;\n}\n\n.styled-table tbody tr:last-of-type {\n    border-bottom: 2px solid #009879;\n}\n.styled-table tbody tr.active-row {\n    font-weight: bold;\n    color: #009879;\n}\n</style>\n"
  tabela_html = tabela.to_html(index=False)
  # Override pandas default and styles:
  tabela_html = re.sub('class="dataframe"', 'class="styled-table" ', tabela_html)
  tabela_html = re.sub('style="text-align: right;"', '', tabela_html)
  tabela_html = re.sub('border="1"', '', tabela_html)
  # Restringir o tamanho do campo Titulo (que contem descricao da patente e pode tomar muito espaco em tela)
  tabela_html = re.sub('<th>Titulo</th>', '<th style="width: 20%;">Titulo</th>', tabela_html)
  footer = "</body>\n</html>"
  with open('PATENTES.html', 'w+') as html_formatado:
    html_formatado.write(header + style + tabela_html + footer)
  print('Arquivo criado com sucesso e disponivel em ./PATENTES_HTML/PATENTES.html')

def create_DT_html(tabela):
  '''Chama createDT.r para criar uma tabela interativa'''
  tabela.to_csv('patentes.csv', index=False)
  subprocess.call (['Rscript', '--vanilla', 'createDT.r'])
# ========================#
# End of helper functions #
# ========================#

if __name__ == '__main__':
  main()
