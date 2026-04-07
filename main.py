from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import sqlite3

app = FastAPI()
DB_NAME = "barbearia.db"

@app.get("/")
def home():
    return FileResponse("index.html")

@app.post("/init-db")
def init_db():
    conn = sqlite3.connect(DB_NAME, timeout=5)
    c = conn.cursor()
    
    # Tabela 1: Guarda apenas quem são os profissionais
    c.execute("CREATE TABLE IF NOT EXISTS Barbeiros (Id INTEGER PRIMARY KEY, Nome TEXT)")
    
    # Tabela 2: Guarda TODOS os horários. O "BarbeiroId" é o que separa a agenda de um da agenda do outro.
    c.execute("CREATE TABLE IF NOT EXISTS Agendamentos (Id INTEGER PRIMARY KEY, BarbeiroId INTEGER, Horario TEXT, Status TEXT, Cliente TEXT)")
    
    c.execute("DELETE FROM Barbeiros")
    c.execute("DELETE FROM Agendamentos")
    
    barbeiros = ['Marcos', 'Junior']
    # Horários formatados de forma simples
    horarios_trabalho = ['08:00 às 09:00', '09:00 às 10:00', '10:00 às 11:00', '11:00 às 12:00', '13:00 às 14:00', '14:00 às 15:00', '15:00 às 16:00', '16:00 às 17:00']
    
    for nome_barbeiro in barbeiros:
        c.execute("INSERT INTO Barbeiros (Nome) VALUES (?)", (nome_barbeiro,))
        barbeiro_id = c.lastrowid # Pega o ID (1 pro Marcos, 2 pro Junior)
        
        for hora in horarios_trabalho:
            # Cria a agenda individual vinculando o horário ao ID do barbeiro
            c.execute("INSERT INTO Agendamentos (BarbeiroId, Horario, Status, Cliente) VALUES (?, ?, 'Livre', '')", (barbeiro_id, hora))
    
    conn.commit()
    conn.close()
    return {"status": "ok", "message": "Banco criado! Agendas independentes para Marcos e Junior."}

@app.get("/barbeiros")
def listar_barbeiros():
    conn = sqlite3.connect(DB_NAME, timeout=5)
    c = conn.cursor()
    c.execute("SELECT Id, Nome FROM Barbeiros")
    linhas = c.fetchall()
    conn.close()
    return [{"id": linha[0], "nome": linha[1]} for linha in linhas]

@app.get("/horarios-livres")
def listar_horarios_livres(barbeiro_id: int):
    conn = sqlite3.connect(DB_NAME, timeout=5)
    c = conn.cursor()
    # Busca SÓ os horários do barbeiro específico que o cliente clicou
    c.execute("SELECT Horario FROM Agendamentos WHERE BarbeiroId = ? AND Status = 'Livre' ORDER BY Horario", (barbeiro_id,))
    linhas = c.fetchall()
    conn.close()
    return [linha[0] for linha in linhas]

@app.post("/agendar")
def agendar_horario(cliente_nome: str, barbeiro_id: int, horario: str):
    conn = sqlite3.connect(DB_NAME, timeout=5)
    c = conn.cursor()
    
    try:
        # INÍCIO DA TRANSAÇÃO E CONTROLE DE CONCORRÊNCIA
        c.execute('BEGIN IMMEDIATE;') 
        
        # Procura a linha exata cruzando o Barbeiro + Horário escolhido
        c.execute("SELECT Id, Status FROM Agendamentos WHERE BarbeiroId = ? AND Horario = ?", (barbeiro_id, horario))
        row = c.fetchone() 
        
        if not row:
            raise ValueError("Erro: Este horário não existe para este barbeiro.")
            
        agendamento_id = row[0]
        status_atual = row[1]
            
        if status_atual == 'Reservado':
            raise ValueError(f"Conflito: O horário das {horario} acabou de ser reservado por outra pessoa!")
            
        # Atualiza apenas a linha específica
        c.execute("UPDATE Agendamentos SET Status = 'Reservado', Cliente = ? WHERE Id = ?", (cliente_nome, agendamento_id))
        
        conn.commit()
        return {"status": "sucesso", "message": f"Agendamento confirmado para {cliente_nome} às {horario}!"}
        
    except ValueError as ve:
        conn.rollback()
        raise HTTPException(status_code=409, detail=str(ve))
    except sqlite3.OperationalError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Erro de banco de dados: {e}")
    finally:
        conn.close()