from flask import Flask, request, make_response, jsonify
from flask import send_from_directory
from flask_cors import cross_origin
from datetime import date, datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
import mysql.connector
import os

# Carregando as variaveis de ambiente, evitar expor no código as infos de conexão.
load_dotenv()

# Conexão com o bando de dados.
mydb = mysql.connector.connect( 
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_DATABASE")
)

try:
  if mydb.is_connected():
    print(" * Log: Conectado ao banco de dados!")
  else:
    print(" * Log: Falha ao conectar ao banco de dados!")
except mysql.connector.Error as err:
  print("Erro:", err)

# Inicializa o aplicativo.
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# METODOS GET - Consultas do banco de dados.

@app.route('/')
def teste():
  return "<p><h1> Aplicação online </h1></p>"

#Retorna o icone para o navegador
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static/'), 'favicon.ico',mimetype='image/vnd.microsoft.icon')

#Verifica se o usuário e senha no banco de dados (se existe e a senha confirma se retorna)
#-- Precisa fornecer o email em caixa baixa e a hash SHA1 da senha
@app.route('/logar=<email>/<hash>')
def logar(email, hash):
  
  cursor = mydb.cursor()

  sql  = """SELECT id_atend, ds_senha FROM tb_atendente WHERE LOWER(ds_email) = LOWER(%(email_str)s) """
    
  cursor.execute(sql, {'email_str': email})
  resultado = cursor.fetchall()

  if not(resultado):
    return make_response( 
      jsonify(
        mensagem='Acesso negado',
      ), 403
    )

  if resultado[0][1] == hash:
    itens = list()
    itens.append(
      {     
        'id': resultado[0][0],
        'Auth': True
      }
    )

    return make_response( 
      jsonify(
        mensagem='Login liberado',
        dados=itens
      ), 200
    )
    
  else:
    return make_response( 
      jsonify(
        mensagem='Acesso negado',
      ), 403
    )
    
#Consulta a tabela de requisições - Teste do banco de dados.
@app.route('/audit', methods=['GET'])
def retornarRegistros():
  
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()

  #Forma compacta de escrever a query.
  sql  = """
          SELECT    A.id_req, 
                    CAST(A.hr_inicio AS CHAR) AS hr_inicio, 
                    CAST(A.hr_atend AS CHAR) AS hr_atend, 
                    CAST(A.hr_fim AS CHAR) AS hr_fim, 
                    CAST(A.dt_data AS CHAR) AS dt_data, 
                    B.ds_guiche, 
                    C.ds_numat, 
                    D.ds_status 
          FROM      pi2_sisat.tb_requisicao A, 
                    pi2_sisat.tb_atendente B, 
                    pi2_sisat.tb_cliente C, 
                    pi2_sisat.tb_status D 
          WHERE     A.id_atend = B.id_atend 
            AND     A.id_cliente = C.id_cliente 
            AND     A.id_status = D.id_status 
          ORDER BY  A.id_req;"""

  #Carrega a query no cursor
  cursor.execute(sql)

  #Busca os dados no banco de dados
  resultado = cursor.fetchall()

  # Se o resultado não for vazio, retornar os dados da requisição
  if resultado:
    itens = list()
    for item in resultado:
      itens.append(
        {     
          'id': item[0],
          'hr_ini': item[1],
          'hr_atend': item[2],
          'hr_fim': item[3],
          'data': item[4],
          'guiche': item[5],
          'código': item[6],
          'status': item[7]
        }
      )

    return make_response( 
      jsonify(
          mensagem='Base de Auditoria',
          dados=itens
        ), 200
     )
    
  # Se o resultado for vazio, retornar None
  else:
    return make_response( 
      jsonify(
        mensagem='Dados não encontrados',
      ), 403
    )

#Consulta do painel - Fila de atendimento apenas código
@app.route('/painel', methods=['GET'])
def registrosPainel():
  
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()

  #Forma compacta de escrever a query.
  sql  = """
        SELECT    B.ds_numat, B.id_cliente
        FROM      pi2_sisat.tb_requisicao A,
                  pi2_sisat.tb_cliente B,
                  pi2_sisat.tb_status C
        WHERE     A.id_cliente = B.id_cliente
          AND     A.id_status = C.id_status
          AND     C.ds_status = "ESPERA"
        ORDER BY  B.fg_prioridade;
      """

  #Carrega a query no cursor
  cursor.execute(sql)

  #Busca os dados no banco de dados
  resultado = cursor.fetchall()

  # Se o resultado não for vazio, retornar os dados da requisição
  if resultado:
    itens = list()
    for item in resultado:
      itens.append(
        {     
          'ds_cliente': item[0],
          'id_cliente': item[1]
        }
      )

    return make_response( 
      jsonify(
          mensagem='Base de Auditoria',
          dados=itens
        ), 200
     )
    
  # Se o resultado for vazio, retornar None
  else:
    return make_response( 
      jsonify(
        mensagem='Dados não encontrados',
      ), 403
    )

#Consulta de id - Proxima requisição (incrementa +1 antes de no ds_codigo)
@app.route('/requisicao', methods=['GET'])
def proximaRequisicao():
  
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()

  #Forma compacta de escrever a query.
  sql  = """
        SELECT    A.id_req
        FROM      pi2_sisat.tb_requisicao A,
                  pi2_sisat.tb_cliente B,
                  pi2_sisat.tb_status C
        WHERE     A.id_cliente = B.id_cliente
            AND   A.id_status = C.id_status
            AND   C.ds_status = "ESPERA"
        ORDER BY  B.fg_prioridade
      """

  #Carrega a query no cursor
  cursor.execute(sql)

  #Busca os dados no banco de dados
  resultado = cursor.fetchall()

  # Se o resultado não for vazio, retornar os dados da requisição
  if resultado:
    itens = list()
    for item in resultado:
      itens.append(
        {     
          'id_req': item[0]
        }
      )

    return make_response( 
      jsonify(
          mensagem='Base de Auditoria',
          dados=itens
        ), 200
     )
    
  # Se o resultado for vazio, retornar None
  else:
    return make_response( 
      jsonify(
        mensagem='Dados não encontrados',
      ), 403
    )

@app.route('/teste', methods=['GET'])
def testeConsulta():
 
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()

  #Forma compacta de escrever a query.
  sql  = """
        SELECT    A.id_req
        FROM      pi2_sisat.tb_requisicao A,
                  pi2_sisat.tb_cliente B,
                  pi2_sisat.tb_status C
        WHERE     A.id_cliente = B.id_cliente
            AND   A.id_status = C.id_status
            AND   C.ds_status = "ESPERA"
        ORDER BY  B.fg_prioridade
      """

  #Carrega a query no cursor
  cursor.execute(sql)

  #Busca os dados no banco de dados
  resultado = cursor.fetchall()
  cod = int(resultado[0][0])
  cod += 1
  
  if cod < 10:
    ds_numat = "000" + str(cod)
  elif cod > 9 and cod < 100:
    ds_numat = "00" + str(cod)
  elif cod > 99 and cod < 1000:
    ds_numat = "0" + str(cod)
  else:
    ds_numat = str(cod)
  
  ds_numat = "B" + ds_numat
  
  print(ds_numat)

  return make_response( 
    jsonify(
      mensagem='Deu certo isso!'
      ), 200
    )

#INSERTS - POST

#NOVO CLIENTE CONVENCIONAL E PRIORITÁRIO: ______________________________________________
#Requisição e cadastro de cliente funcionam juntas (entra o cliente e gera a requisição)
#Existe uma terceira consulta antes de prosseguir que consiste em formular o codigo
#de atendimento para o novo cliente, que também será diferente entre as consultas.

#Método para ambos: ____________________________________________________________________
#Insere um cliente comum na fila para atendimento.
@app.route('/novoCliente=<tipo>', methods=['POST'])
def postCliente(tipo):
    
  #Variavel de código para atendimento.
  ds_numat = "X0000"

  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()

  #Forma compacta de escrever a query - Aqui pegamos o ultimo registro na tabela de clientes. 
  sql  = "SELECT id_cliente FROM tb_cliente ORDER BY id_cliente DESC LIMIT 1"

  #Carrega a query no cursor
  cursor.execute(sql)

  #Separamos o ID do ultimo cliente e incrementamos 1.
  resultado = cursor.fetchall()
  cod = int(resultado[0][0])
  cod += 1
  
  #Tratamos o texto para ficar com casas à esquerda.
  if cod < 10:
    ds_numat = "000" + str(cod)
  elif cod > 9 and cod < 100:
    ds_numat = "00" + str(cod)
  elif cod > 99 and cod < 1000:
    ds_numat = "0" + str(cod)
  else:
    ds_numat = str(cod)
  
  #Para fazermos um insert UNICO no banco é diferente de multiplos atenção abaixo.
  sql = "INSERT INTO tb_cliente (fg_prioridade, ds_numat) "

  #Dependendo do argumento passado no "POST" faremos um registro diferente no banco de dados.
  #Caso tipo seja igual a '1' temos um atendimento convencional, caso contrário prioritário.
  if tipo == '1':
    ds_numat = "B" + str(ds_numat)
    sql += "VALUES (1, %(ds_numat)s); "
  else:
    ds_numat = "A" + str(ds_numat)
    sql += "VALUES (0, %(ds_numat)s); "

  #Tentamos executar o código SQL com os dados carregados
  try:
    #Carregamos em data o código de atendimento já produzido.
    cursor.execute(sql, { 'ds_numat': ds_numat })
    mydb.commit()
    postReq(ds_numat)
    
  except Exception as error:

    print(error)
    return make_response( 
      jsonify(
          mensagem= error
      ), 403
    )
    
  else:        
    return make_response( 
      jsonify(
        mensagem='Serviço atualizado com sucesso!'
        ), 200
    )

#Insere nova requisição para um cliente específico.
#perceba que não tem rota aqui no método.Trata-se de uma função de apoio de cadastro
#nesse caso ela acontece na sequência do cadastro do cliente (conforme regra de negócio).
def postReq(argumento):

  ds_numat = str(argumento)
  
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()
  
  #Forma compacta de escrever a query conslultando o id de um cliente específico.
  sql = "SELECT id_cliente FROM tb_cliente WHERE ds_numat = %(ds_numat)s "

  #Carrega a query no cursor
  cursor.execute(sql, { 'ds_numat': str(ds_numat) })

  #Busca o id_cliente de um cliente específico
  resultado = cursor.fetchall()
  id_cliente = int(resultado[0][0])
 
  #Lançamos um registro na tabela de requisição com o id_cliente informado.  
  sql =  "INSERT INTO tb_requisicao (hr_inicio, hr_atend, hr_fim, dt_data, id_status, id_cliente, id_atend) "
  sql += "VALUES (CURRENT_TIME(), '00:00:00', '00:00:00', CURRENT_DATE(), 1, %(id_cliente)s, 1); "

  #Tentamos executar o código SQL com os dados carregados
  try:
    #Carregamos em data o código de atendimento já produzido.
    cursor.execute(sql, { 'id_cliente': id_cliente })
    mydb.commit()
    
  except Exception as error:

    return print(error)
    
  else:        
    return print("Log: Requisição cadastrada com sucesso - Novo cliente disponível")

#UPDATE - PUT:
#Elencar para atendimento.
@app.route('/chamarCliente=<id_atend>', methods=['PUT'])
def chamarCliente(id_atend):
  
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()
  
  #Capturamos a ultima requisição disponivel no banco conforme regras de negócio.
  sql = """
           SELECT     A.id_req 
           FROM       pi2_sisat.tb_requisicao A,
                      pi2_sisat.tb_cliente B,
                      pi2_sisat.tb_status C

           WHERE      A.id_cliente = B.id_cliente
              AND     A.id_status = C.id_status
              AND     C.ds_status = "ESPERA"

            ORDER BY  B.fg_prioridade LIMIT 1;"""
  
  cursor.execute(sql)
  resultado = cursor.fetchall()
  
  #Reservamos o id desta requisição, pois é ela que recebera a atualização
  id_req = int(resultado[0][0])

  #Vamos atualizar a requisição vinculando ao guiche de atendimento
  sql = "UPDATE tb_requisicao SET id_atend = %s WHERE id_req = %s"
  data = (int(id_atend), int(id_req))

  try:
    #Carrega a query no cursor
    cursor.execute(sql, data)
    mydb.commit()
  
  except Exception as error:

    print(error)
    return make_response( 
      jsonify(
          mensagem= error
      ), 403
    )
    
  else:        
    return make_response( 
      jsonify(
        mensagem='Cliente atribuido ao guichê!'
        ), 200
    )

# Iniciar o atendimento da requisição
@app.route('/atenderCliente=<id_atend>', methods=['PUT'])
def atenderCliente(id_atend):
  
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()
  
  #Capturamos a ultima requisição disponivel no banco conforme regras de negócio.
  sql = """
           SELECT     A.id_req 
           FROM       pi2_sisat.tb_requisicao A,
                      pi2_sisat.tb_cliente B,
                      pi2_sisat.tb_status C

           WHERE      A.id_cliente = B.id_cliente
              AND     A.id_status = C.id_status
              AND     C.ds_status = 'ESPERA'

            ORDER BY  B.fg_prioridade LIMIT 1;"""
  
  cursor.execute(sql)
  resultado = cursor.fetchall()

  #Reservamos o id desta requisição, pois é ela que recebera a atualização
  id_req = int(resultado[0][0])

  #Vamos atualizar a requisição vinculando ao guiche de atendimento
  sql = "UPDATE tb_requisicao SET hr_atend = CURRENT_TIME(), id_status = 2, id_atend = %s WHERE id_req = %s"
  data = (int(id_atend), int(id_req))

  try:
    #Carrega a query no cursor
    cursor.execute(sql, data)
    mydb.commit()
  
  except Exception as error:

    print(error)
    return make_response( 
      jsonify(
          mensagem= error
      ), 403
    )
    
  else:        
    return make_response( 
      jsonify(
        mensagem='Cliente em atendimento no guiche!'
        ), 200
    )
  
#Encerrar o atendimento da requisição
@app.route('/concluirAtendimento=<id_atend>', methods=['PUT'])
def encerrarCliente(id_atend):
  
  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()
  
  #Capturamos a requisição em atendimento pelo guiche
  sql = """
           SELECT     A.id_req 
           FROM       pi2_sisat.tb_requisicao A,
                      pi2_sisat.tb_cliente B,
                      pi2_sisat.tb_status C

           WHERE      A.id_cliente = B.id_cliente
              AND     A.id_status = C.id_status
              AND     C.ds_status = "ATENDIMENTO"
              AND     A.id_atend = %(id_atend)s

            ORDER BY  B.fg_prioridade LIMIT 1 """
  
  cursor.execute(sql, { 'id_atend': int(id_atend)})
  resultado = cursor.fetchall()
  
  #Reservamos o id desta requisição, pois é ela que recebera a atualização.
  id_req = int(resultado[0][0])

  #Vamos atualizar a requisição vinculanda ao guiche.
  sql = "UPDATE tb_requisicao SET hr_fim = CURRENT_TIME(), id_status = 3 WHERE id_req = %s "
  data = (int(id_req), )

  try:
    #Carrega a query no cursor.
    cursor.execute(sql, data)
    mydb.commit()
  
  except Exception as error:

    print(error)
    return make_response( 
      jsonify(
          mensagem= error
      ), 403
    )
    
  else:        
    return make_response( 
      jsonify(
        mensagem='Atendimento encerrado!'
        ), 200
    )

#Cancelar o atendimento da requisição
@app.route('/cancelarAtendimento=<id_req>', methods=['PUT'])
def cancelarRequisicao(id_req):

  #Instancia um cursor no banco de dados.
  cursor = mydb.cursor()
  
  #Vamos atualizar a requisição vinculanda ao guiche.
  sql = "UPDATE tb_requisicao SET hr_fim = CURRENT_TIME(), id_status = 4 WHERE id_req = %s "
  data = (int(id_req), )

  try:
    #Carrega a query no cursor.
    cursor.execute(sql, data)
    mydb.commit()
  
  except Exception as error:

    print(error)
    return make_response( 
      jsonify(
          mensagem= error
      ), 403
    )
    
  else:        
    return make_response( 
      jsonify(
        mensagem='Atendimento cancelado!'
        ), 200
    )

# Garante que app sera iniciado quado o escopo "main"
# for empilhado na fila de execução do interpretador
if (__name__ == '__main__'):
    app.run()