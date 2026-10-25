import { ChangeEvent, FormEvent, useEffect, useMemo, useState } from 'react';
import './index.css';

type Transaction = {
  id: number;
  data: string;
  valor: string;
  descricao: string;
};

type Filter = 'todas' | 'entradas' | 'saidas';
type SortOrder = 'recentes' | 'antigas';

const API_URL = (
  process.env.REACT_APP_API_URL || 'http://localhost:5000'
).replace(/\/$/, '');

const currency = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

function App() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [filter, setFilter] = useState<Filter>('todas');
  const [sortOrder, setSortOrder] = useState<SortOrder>('recentes');
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  useEffect(() => {
    async function loadTransactions() {
      try {
        const response = await fetch(`${API_URL}/api/movimentacoes`);
        const result = await response.json();
        if (!response.ok) {
          throw new Error(result.erro || 'Não foi possível carregar as movimentações.');
        }
        setTransactions(result.movimentacoes);
      } catch (loadError) {
        setError(
          loadError instanceof Error
            ? loadError.message
            : 'Não foi possível conectar à API.',
        );
      } finally {
        setLoading(false);
      }
    }

    void loadTransactions();
  }, []);

  const visibleTransactions = useMemo(() => {
    return transactions
      .filter((transaction) => {
        const amount = Number(transaction.valor);
        if (filter === 'entradas') return amount > 0;
        if (filter === 'saidas') return amount < 0;
        return true;
      })
      .sort((first, second) => {
        const comparison = first.data.localeCompare(second.data);
        return sortOrder === 'recentes' ? -comparison : comparison;
      });
  }, [transactions, filter, sortOrder]);

  const totalEntries = transactions
    .filter((transaction) => Number(transaction.valor) > 0)
    .reduce((total, transaction) => total + Number(transaction.valor), 0);
  const totalOutflows = transactions
    .filter((transaction) => Number(transaction.valor) < 0)
    .reduce((total, transaction) => total + Math.abs(Number(transaction.valor)), 0);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0] || null;
    setSelectedFile(file);
    setError('');
    setNotice('');
  }

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!selectedFile) {
      setError('Escolha um arquivo OFX antes de importar.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);
    setUploading(true);
    setError('');
    setNotice('');

    try {
      const response = await fetch(`${API_URL}/api/movimentacoes/importar`, {
        method: 'POST',
        body: formData,
      });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.erro || 'Não foi possível importar o arquivo.');
      }
      setTransactions(result.movimentacoes);
      setNotice(
        `${result.inseridas} movimentação(ões) importada(s)` +
          (result.duplicadas > 0
            ? `; ${result.duplicadas} duplicada(s) ignorada(s).`
            : '.'),
      );
      setSelectedFile(null);
      form.reset();
    } catch (uploadError) {
      setError(
        uploadError instanceof Error
          ? uploadError.message
          : 'Não foi possível conectar à API.',
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <main className="page-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Seus Extratos, início">
          seus-extratos<span>.com</span>
        </a>
        <p className="topbar-message">Confira e organize seus extratos bancários!</p>
      </header>

      <section className="intro" aria-labelledby="page-title">
        <form className="upload-card" onSubmit={handleUpload}>
          <label className="file-picker" htmlFor="ofx-file">
            <span className="upload-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 15v4h14v-4" />
              </svg>
            </span>
            <span className="file-picker-title">
              {selectedFile ? 'Arquivo selecionado' : 'Escolha seu arquivo OFX'}
            </span>
            <span className="file-picker-hint">
              {selectedFile ? selectedFile.name : 'Clique para procurar no dispositivo'}
            </span>
            <input
              id="ofx-file"
              type="file"
              accept=".ofx,application/x-ofx"
              onChange={handleFileChange}
            />
          </label>
          <button className="upload-button" type="submit" disabled={uploading}>
            {uploading ? 'Importando...' : 'Importar extrato'}
          </button>
        </form>
      </section>

      {error && (
        <div className="feedback feedback-error" role="alert">
          {error}
        </div>
      )}
      {notice && (
        <div className="feedback feedback-success" role="status">
          {notice}
        </div>
      )}

      <section className="summary" aria-label="Resumo das movimentações">
        <article className="summary-card">
          <span className="summary-label">Movimentações</span>
          <strong>{transactions.length}</strong>
          <span className="summary-detail">registradas no extrato</span>
        </article>
        <article className="summary-card">
          <span className="summary-label">Entradas</span>
          <strong className="amount-positive">{currency.format(totalEntries)}</strong>
          <span className="summary-detail">valores recebidos</span>
        </article>
        <article className="summary-card">
          <span className="summary-label">Saídas</span>
          <strong className="amount-negative">{currency.format(totalOutflows)}</strong>
          <span className="summary-detail">valores pagos</span>
        </article>
      </section>

      <section className="transactions-panel" aria-labelledby="transactions-title">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">SEU HISTÓRICO</p>
            <h2 id="transactions-title">Movimentações</h2>
          </div>
          <div className="table-controls">
            <div className="filter-tabs" aria-label="Filtrar movimentações">
              {([
                ['todas', 'Todas'],
                ['entradas', 'Entradas'],
                ['saidas', 'Saídas'],
              ] as const).map(([value, label]) => (
                <button
                  className={filter === value ? 'filter-tab active' : 'filter-tab'}
                  key={value}
                  type="button"
                  aria-pressed={filter === value}
                  onClick={() => setFilter(value)}
                >
                  {label}
                </button>
              ))}
            </div>
            <label className="sort-control">
              <span>Ordenar</span>
              <select
                aria-label="Ordenar por data"
                value={sortOrder}
                onChange={(event) => setSortOrder(event.target.value as SortOrder)}
              >
                <option value="recentes">Mais recentes</option>
                <option value="antigas">Mais antigas</option>
              </select>
            </label>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th scope="col">Data</th>
                <th scope="col">Descrição</th>
                <th scope="col" className="value-column">Valor</th>
                <th scope="col">Tipo</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td className="table-message" colSpan={4}>Carregando movimentações...</td>
                </tr>
              ) : visibleTransactions.length === 0 ? (
                <tr>
                  <td className="table-message" colSpan={4}>
                    {transactions.length === 0
                      ? 'Suas movimentações aparecerão aqui após importar um arquivo OFX.'
                      : 'Nenhuma movimentação encontrada para este filtro.'}
                  </td>
                </tr>
              ) : (
                visibleTransactions.map((transaction) => {
                  const incoming = Number(transaction.valor) > 0;
                  return (
                    <tr key={transaction.id}>
                      <td className="date-cell">
                        {new Intl.DateTimeFormat('pt-BR').format(
                          new Date(`${transaction.data}T00:00:00`),
                        )}
                      </td>
                      <td className="description-cell">{transaction.descricao}</td>
                      <td className={`value-cell ${incoming ? 'amount-positive' : 'amount-negative'}`}>
                        {currency.format(Number(transaction.valor))}
                      </td>
                      <td>
                        <span className={`type-badge ${incoming ? 'badge-incoming' : 'badge-outgoing'}`}>
                          {incoming ? 'Entrada' : 'Saída'}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
        {!loading && transactions.length > 0 && (
          <p className="table-footer">
            Exibindo {visibleTransactions.length} de {transactions.length} movimentações
          </p>
        )}
      </section>
      <footer className="page-footer">Seus extratos bancários organizados com praticidade.</footer>
    </main>
  );
}

export default App;
