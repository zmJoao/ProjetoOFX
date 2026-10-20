CREATE TABLE IF NOT EXISTS movimentacoes (
    id SERIAL PRIMARY KEY,
    data_movimentacao DATE,
    valor NUMERIC(15,2),
    descricao VARCHAR(255)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_movimentacoes_data_valor_descricao
ON movimentacoes (data_movimentacao, valor, descricao);
