# Sistema de Agendamento para Barbearia

Projeto desenvolvido como requisito para a disciplina de Banco de Dados 2. O foco principal deste projeto e demonstrar a aplicacao pratica de controle de concorrencia, propriedades ACID e transacoes explicitas em um banco de dados relacional integrado a um backend.

## Escopo do Projeto

O sistema simula o agendamento de horarios em uma barbearia com multiplos profissionais. O desafio principal resolvido pela aplicacao e garantir que, em um cenario de multiplos acessos simultaneos, um mesmo horario nao possa ser reservado por duas pessoas diferentes. 

## Tecnologias Utilizadas

* Backend: Python com framework FastAPI
* Banco de Dados: SQLite3 (Relacional)
* Frontend: HTML5, CSS3 e JavaScript (Vanilla)
* Servidor: Uvicorn

## Arquitetura do Banco de Dados

O banco de dados (SQLite) foi modelado utilizando duas tabelas principais para garantir a separacao de contextos e normalizacao basica (relacao 1:N):

1. Tabela Barbeiros
   * Id (INTEGER PRIMARY KEY)
   * Nome (TEXT)

2. Tabela Agendamentos
   * Id (INTEGER PRIMARY KEY)
   * BarbeiroId (INTEGER) - Chave Estrangeira logica referenciando o Barbeiro
   * Horario (TEXT)
   * Status (TEXT) - Define se o horario esta 'Livre' ou 'Reservado'
   * Cliente (TEXT) - Nome do cliente que efetuou a reserva

A separacao permite que cada barbeiro possua sua propria grade de horarios de forma independente.

## Controle de Concorrencia e Transacoes

O coracao do projeto esta na rota de agendamentos (`/agendar`), onde o controle de concorrencia pessimista foi implementado para garantir a integridade dos dados:

1. Bloqueio de Escrita (Lock): A transacao e iniciada com o comando `BEGIN IMMEDIATE;`. Isso garante que o motor do banco de dados adquira um lock exclusivo de escrita imediatamente. Transacoes concorrentes no mesmo milissegundo sao colocadas em fila, prevenindo o fenomeno de "Lost Update" (Atualizacao Perdida).
2. Leitura e Validacao: Dentro da transacao segura, o sistema verifica se o status da linha cruzada (BarbeiroId + Horario) ainda e 'Livre'. 
3. Atomicidade (Commit/Rollback): 
   * Caso o horario esteja livre, o `UPDATE` e executado e a transacao e confirmada com `commit()`, garantindo a durabilidade e liberando o lock.
   * Caso o horario ja tenha sido ocupado por uma transacao anterior na fila, ou ocorra qualquer erro de logica, o `rollback()` e imediatamente acionado, retornando o banco ao seu estado original seguro e disparando um erro HTTP 409 (Conflict).

## Como Executar o Projeto Localmente

### Pre-requisitos
Certifique-se de ter o Python 3 instalado em sua maquina.

### Passo a passo

1. Clone este repositorio em sua maquina local.
2. Abra o terminal na pasta raiz do projeto.
3. Instale as dependencias necessarias executando o comando:
   ```bash
   pip install fastapi uvicorn