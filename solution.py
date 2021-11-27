import glob
import os
import re
import lxml
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import numpy as np

def main():
  ''' Creates and populates a DataFrame with info from patents html files. Calls functions for html file validation, and writes a HTML on a created ./PATENTES_HTML subdirectory'''
  # Criar boiler plate para o DataFrame
  tabela = pd.DataFrame(columns=['Arquivo','CNPJ','Resultado','No_pedido','Deposito','Titulo','IPC','Aviso'])
  files = glob.glob('*.html')
  assert files != [], "Diretorio atual nao contem arquivos HTML"
  
  for file in files:
    with open(file, 'r', encoding='latin-1') as html_file:
      content = html_file.read()
      soup = BeautifulSoup(content, 'lxml') #  melhor que o html_parser do bs4
      cnpj = get_cnpj_or_cpf(soup)
      # Ha pedido de patente para este CPF/CNPJ?
      pedidos = re.search('Pedido', soup.text)
      if pedidos == None:
        # Se nao ha, popular DataFrame com informacoes basicas
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
          parsed_table['Aviso'] = "Ha mais registros de patente para este CNPJ!"
        tabela = tabela.append(parsed_table)
  tabela.fillna('-', inplace=True) # Padronizando NAs
  tabela.replace('-', '', inplace=True)
  
  # Just create the html
  create_html_file(tabela)

# =======================#
# Begin helper functions #
# =======================#
def is_valid_html(soup):
  ''' Search for the string - CPF ou CNPJ do Depositante word Depositante - abort execution if none '''
  depositante_string = re.search('CPF ou CNPJ do Depositante:', soup.text)
  if depositante_string == None:
    print('html invalido:' + file + '. Por favor, mantenha no diretorio apenas arquivos html de patentes')
    raise Exception("HTML provavelmente nao se refere a base de dados de patente")

def get_cnpj_or_cpf(soup):
  ''' Pega um buffer depois da palavra Depositante e remover char nao numericos'''
  is_valid_html(soup)
  depositante = re.search('Depositante:', soup.text)
  initial_string_position = depositante.span()[1] + 1
  final_string_position = depositante.span()[1] + 20
  cnpj = soup.text[initial_string_position : final_string_position]
  cnpj = re.sub('[^0-9]', '', cnpj) # remover tudo que nao for numero
  return cnpj

def create_html_file(tabela):
  ''' Adiciona CSS stylesheet e cria o arquivo html'''
  # Styling HTML file with CSS
  header = "<body>\n<html>\n<style>\n"
  style = "table {\nborder-collapse: collapse;\nmargin: 25px\nfont-size: 0.9em;\nfont-family: sans-serif;\nmin-width: 400px;\nbox-shadow: 0 0 20px rgba(0, 0, 0, 0.15);\n}\ntable thead tr {\nbackground-color: #009879;\ncolor: #ffffff;\ntext-align: left;\n}\nth,\ntd {\npadding: 12px 15px;\n}\ntable tbody tr {\nborder-bottom: 1px solid #dddddd;\n}\n</style>"
  tabela_html = tabela.to_html(index=False)
  footer = "</body>\n</html>"
  if not os.path.exists('./PATENTES_HTML/'):
    os.mkdir('./PATENTES_HTML/')
  os.chdir('./PATENTES_HTML/')
  with open('PATENTES.html', 'w+') as html_formatado:
    html_formatado.write(header + style + tabela_html + footer)
  print('Arquivo criado com sucesso e disponivel em ./PATENTES_HTML/PATENTES.html')

# ========================#
# End of helper functions #
# ========================#

if __name__ == '__main__':
  main()
