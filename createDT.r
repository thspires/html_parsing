# Cria tabela interativa com os dados obtidos
# Usa o pacot DT: interface to the JavaScript library DataTables
DT_instalado <- 'DT' %in% rownames(installed.packages())
if (DT_instalado == FALSE) {
  readline(prompt="Permitir instalacao do pacote DT? [enter] p/ continuar [ctrl+c] para abortar")
  install.packages('DT')
}
df <- read.csv('patentes.csv')
df <- DT::datatable(df)
DT::saveWidget(df, './PATENTES_HTML/patentes_DT.html', selfcontained = FALSE)
