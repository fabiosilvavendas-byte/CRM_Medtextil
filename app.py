import React, { useState, useMemo } from 'react';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Search, Download, TrendingUp, Users, DollarSign, AlertCircle, Package, Calendar } from 'lucide-react';

const GestaoComercial = () => {
  const [activeModule, setActiveModule] = useState('bi');
  const [dateRange, setDateRange] = useState({ start: '2024-01-01', end: '2024-12-31' });
  const [selectedVendor, setSelectedVendor] = useState('todos');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedClient, setSelectedClient] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState(null);

  // Dados de exemplo simulando as planilhas
  const vendas = [
    { Vendedor: 'João Silva', RazaoSocial: 'Empresa A', CPF_CNPJ: '12345678000190', DataEmissao: '2024-03-15', CodigoProduto: 'P001', Quantidade: 100, PrecoUnit: 50, TotalLiquidoNF: 5000, CondPagamento: '30 dias' },
    { Vendedor: 'Maria Santos', RazaoSocial: 'Empresa B', CPF_CNPJ: '98765432000110', DataEmissao: '2024-03-20', CodigoProduto: 'P002', Quantidade: 50, PrecoUnit: 80, TotalLiquidoNF: 4000, CondPagamento: '60 dias' },
    { Vendedor: 'João Silva', RazaoSocial: 'Empresa C', CPF_CNPJ: '45678912000130', DataEmissao: '2024-04-10', CodigoProduto: 'P001', Quantidade: 150, PrecoUnit: 53, TotalLiquidoNF: 7950, CondPagamento: '45 dias' },
    { Vendedor: 'Pedro Costa', RazaoSocial: 'Empresa A', CPF_CNPJ: '12345678000190', DataEmissao: '2024-05-05', CodigoProduto: 'P003', Quantidade: 200, PrecoUnit: 30, TotalLiquidoNF: 6000, CondPagamento: '30 dias' },
    { Vendedor: 'Maria Santos', RazaoSocial: 'Empresa D', CPF_CNPJ: '78945612000150', DataEmissao: '2024-06-12', CodigoProduto: 'P002', Quantidade: 75, PrecoUnit: 85, TotalLiquidoNF: 6375, CondPagamento: '90 dias' },
  ];

  const produtos = [
    { ID_COD: 'P001', Gramatura: '180g', Descricao: 'Fio 30/1' },
    { ID_COD: 'P002', Gramatura: '220g', Descricao: 'Fio 40/1' },
    { ID_COD: 'P003', Gramatura: '150g', Descricao: 'Fio 24/1' },
  ];

  const tabelaPreco = [
    { ID_COD: 'P001', PRECO: 50 },
    { ID_COD: 'P002', PRECO: 80 },
    { ID_COD: 'P003', PRECO: 30 },
  ];

  const inadimplencia = [
    { 'Vr.Líquido': 5000, 'Dt.Vencimento': '2024-04-15', 'Razão Social': 'Empresa A', 'Funcionário': 'João Silva', 'No Doc': 'NF-001' },
    { 'Vr.Líquido': 4000, 'Dt.Vencimento': '2024-05-20', 'Razão Social': 'Empresa B', 'Funcionário': 'Maria Santos', 'No Doc': 'NF-002' },
    { 'Vr.Líquido': 6375, 'Dt.Vencimento': '2024-09-12', 'Razão Social': 'Empresa D', 'Funcionário': 'Maria Santos', 'No Doc': 'NF-005' },
  ];

  // Conciliação de dados
  const vendasCompletas = useMemo(() => {
    return vendas.map(venda => {
      const produto = produtos.find(p => p.ID_COD === venda.CodigoProduto);
      const preco = tabelaPreco.find(t => t.ID_COD === venda.CodigoProduto);
      return { ...venda, ...produto, PrecoTabela: preco?.PRECO || 0 };
    });
  }, []);

  // Cálculos de KPIs
  const kpis = useMemo(() => {
    const totalFaturamento = vendasCompletas.reduce((acc, v) => acc + v.TotalLiquidoNF, 0);
    const totalClientes = new Set(vendasCompletas.map(v => v.CPF_CNPJ)).size;
    const ticketMedio = totalFaturamento / vendasCompletas.length;
    
    const clientesAtivos = new Set(vendasCompletas.filter(v => {
      const diff = new Date() - new Date(v.DataEmissao);
      return diff < 60 * 24 * 60 * 60 * 1000;
    }).map(v => v.CPF_CNPJ)).size;
    
    const positivacao = (clientesAtivos / totalClientes * 100).toFixed(1);

    return { totalFaturamento, totalClientes, ticketMedio, positivacao };
  }, [vendasCompletas]);

  // Ranking de clientes
  const rankingClientes = useMemo(() => {
    const clienteMap = {};
    vendasCompletas.forEach(v => {
      if (!clienteMap[v.CPF_CNPJ]) {
        clienteMap[v.CPF_CNPJ] = { nome: v.RazaoSocial, total: 0 };
      }
      clienteMap[v.CPF_CNPJ].total += v.TotalLiquidoNF;
    });
    return Object.entries(clienteMap)
      .map(([cnpj, data]) => ({ cnpj, ...data }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10);
  }, [vendasCompletas]);

  // Ranking de vendedores
  const rankingVendedores = useMemo(() => {
    const vendedorMap = {};
    vendasCompletas.forEach(v => {
      if (!vendedorMap[v.Vendedor]) {
        vendedorMap[v.Vendedor] = { total: 0, comissao: 0 };
      }
      vendedorMap[v.Vendedor].total += v.TotalLiquidoNF;
      
      const desconto = ((v.PrecoTabela - v.PrecoUnit) / v.PrecoTabela * 100);
      let taxaComissao = 0.03;
      if (v.PrecoUnit >= v.PrecoTabela * 1.06) taxaComissao = 0.04;
      vendedorMap[v.Vendedor].comissao += v.TotalLiquidoNF * taxaComissao;
    });
    return Object.entries(vendedorMap)
      .map(([vendedor, data]) => ({ vendedor, ...data }))
      .sort((a, b) => b.total - a.total);
  }, [vendasCompletas]);

  // Análise de desconto por vendedor
  const analiseDesconto = useMemo(() => {
    const vendedorMap = {};
    vendasCompletas.forEach(v => {
      if (!vendedorMap[v.Vendedor]) {
        vendedorMap[v.Vendedor] = { totalDesconto: 0, count: 0 };
      }
      const desconto = ((v.PrecoTabela - v.PrecoUnit) / v.PrecoTabela * 100);
      vendedorMap[v.Vendedor].totalDesconto += desconto;
      vendedorMap[v.Vendedor].count += 1;
    });
    return Object.entries(vendedorMap).map(([vendedor, data]) => ({
      vendedor,
      descontoMedio: (data.totalDesconto / data.count).toFixed(2)
    }));
  }, [vendasCompletas]);

  // Clientes sem compras (Churn)
  const clientesChurn = useMemo(() => {
    const hoje = new Date();
    const clientesRecentes = new Set(vendasCompletas.filter(v => {
      const diff = (hoje - new Date(v.DataEmissao)) / (1000 * 60 * 60 * 24);
      return diff <= 60;
    }).map(v => v.CPF_CNPJ));

    const todosClientes = new Set(vendasCompletas.map(v => v.CPF_CNPJ));
    return Array.from(todosClientes).filter(cnpj => !clientesRecentes.has(cnpj))
      .map(cnpj => {
        const cliente = vendasCompletas.find(v => v.CPF_CNPJ === cnpj);
        return cliente.RazaoSocial;
      });
  }, [vendasCompletas]);

  // Evolução mensal
  const evolucaoMensal = useMemo(() => {
    const mesesMap = {};
    vendasCompletas.forEach(v => {
      const mes = v.DataEmissao.substring(0, 7);
      mesesMap[mes] = (mesesMap[mes] || 0) + v.TotalLiquidoNF;
    });
    return Object.entries(mesesMap).map(([mes, valor]) => ({ mes, valor }));
  }, [vendasCompletas]);

  const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981'];

  const exportToCSV = (data, filename) => {
    const csv = [
      Object.keys(data[0]).join(','),
      ...data.map(row => Object.values(row).join(','))
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="fixed left-0 top-0 h-full w-64 bg-white shadow-lg p-6">
        <h1 className="text-2xl font-bold text-blue-600 mb-8">Gestão Comercial</h1>
        
        <nav className="space-y-2">
          <button
            onClick={() => setActiveModule('bi')}
            className={`w-full text-left px-4 py-3 rounded-lg transition ${
              activeModule === 'bi' ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'
            }`}
          >
            <TrendingUp className="inline mr-2" size={20} />
            Relatório BI
          </button>
          <button
            onClick={() => setActiveModule('pedidos')}
            className={`w-full text-left px-4 py-3 rounded-lg transition ${
              activeModule === 'pedidos' ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'
            }`}
          >
            <Package className="inline mr-2" size={20} />
            Pedidos e Comissões
          </button>
          <button
            onClick={() => setActiveModule('inadimplencia')}
            className={`w-full text-left px-4 py-3 rounded-lg transition ${
              activeModule === 'inadimplencia' ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'
            }`}
          >
            <AlertCircle className="inline mr-2" size={20} />
            Inadimplência
          </button>
        </nav>

        {/* Filtros Globais */}
        <div className="mt-8 space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Período</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg text-sm"
            />
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg mt-2 text-sm"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-2">Vendedor</label>
            <select
              value={selectedVendor}
              onChange={(e) => setSelectedVendor(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm"
            >
              <option value="todos">Todos</option>
              {[...new Set(vendas.map(v => v.Vendedor))].map(v => (
                <option key={v} value={v}>{v}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 p-8">
        {/* Módulo BI */}
        {activeModule === 'bi' && (
          <div>
            <h2 className="text-3xl font-bold mb-6">Relatório Comercial Completo</h2>
            
            {/* KPIs */}
            <div className="grid grid-cols-4 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Faturamento Total</p>
                    <p className="text-2xl font-bold text-blue-600">
                      R$ {kpis.totalFaturamento.toLocaleString('pt-BR')}
                    </p>
                  </div>
                  <DollarSign className="text-blue-600" size={32} />
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Total de Clientes</p>
                    <p className="text-2xl font-bold text-green-600">{kpis.totalClientes}</p>
                  </div>
                  <Users className="text-green-600" size={32} />
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Ticket Médio</p>
                    <p className="text-2xl font-bold text-purple-600">
                      R$ {kpis.ticketMedio.toLocaleString('pt-BR')}
                    </p>
                  </div>
                  <TrendingUp className="text-purple-600" size={32} />
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm">Positivação</p>
                    <p className="text-2xl font-bold text-orange-600">{kpis.positivacao}%</p>
                  </div>
                  <Calendar className="text-orange-600" size={32} />
                </div>
              </div>
            </div>

            {/* Gráficos */}
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-bold mb-4">Evolução Mensal de Faturamento</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={evolucaoMensal}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="mes" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line type="monotone" dataKey="valor" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-bold mb-4">Top 5 Clientes</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={rankingClientes.slice(0, 5)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="nome" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="total" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Rankings */}
            <div className="grid grid-cols-2 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-bold mb-4">Ranking de Vendedores</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left">Vendedor</th>
                        <th className="px-4 py-2 text-right">Faturamento</th>
                        <th className="px-4 py-2 text-right">Comissão</th>
                      </tr>
                    </thead>
                    <tbody>
                      {rankingVendedores.map((v, i) => (
                        <tr key={i} className="border-t">
                          <td className="px-4 py-2">{v.vendedor}</td>
                          <td className="px-4 py-2 text-right">R$ {v.total.toLocaleString('pt-BR')}</td>
                          <td className="px-4 py-2 text-right text-green-600">
                            R$ {v.comissao.toLocaleString('pt-BR')}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-bold mb-4">Análise de Desconto por Vendedor</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-2 text-left">Vendedor</th>
                        <th className="px-4 py-2 text-right">Desconto Médio</th>
                      </tr>
                    </thead>
                    <tbody>
                      {analiseDesconto.map((v, i) => (
                        <tr key={i} className="border-t">
                          <td className="px-4 py-2">{v.vendedor}</td>
                          <td className="px-4 py-2 text-right">{v.descontoMedio}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Clientes em Churn */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4">
                Clientes sem Compras (últimos 60 dias) - {clientesChurn.length}
              </h3>
              <div className="flex flex-wrap gap-2">
                {clientesChurn.map((cliente, i) => (
                  <span key={i} className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                    {cliente}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Módulo Pedidos */}
        {activeModule === 'pedidos' && (
          <div>
            <h2 className="text-3xl font-bold mb-6">Módulo de Pedidos e Comissões</h2>
            
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <div className="flex gap-4 items-center mb-4">
                <Search className="text-gray-400" size={20} />
                <input
                  type="text"
                  placeholder="Buscar por Código ou Descrição do Produto..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="flex-1 px-4 py-2 border rounded-lg"
                />
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Código</th>
                      <th className="px-4 py-2 text-left">Descrição</th>
                      <th className="px-4 py-2 text-left">Gramatura</th>
                      <th className="px-4 py-2 text-right">Preço Tabela</th>
                      <th className="px-4 py-2 text-center">Comissão Base</th>
                    </tr>
                  </thead>
                  <tbody>
                    {produtos
                      .filter(p => 
                        p.ID_COD.toLowerCase().includes(searchTerm.toLowerCase()) ||
                        p.Descricao.toLowerCase().includes(searchTerm.toLowerCase())
                      )
                      .map((p, i) => {
                        const preco = tabelaPreco.find(t => t.ID_COD === p.ID_COD);
                        return (
                          <tr key={i} className="border-t hover:bg-gray-50">
                            <td className="px-4 py-3 font-mono">{p.ID_COD}</td>
                            <td className="px-4 py-3">{p.Descricao}</td>
                            <td className="px-4 py-3">{p.Gramatura}</td>
                            <td className="px-4 py-3 text-right font-bold">
                              R$ {preco?.PRECO.toFixed(2)}
                            </td>
                            <td className="px-4 py-3 text-center">
                              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                                3% (4% se +6%)
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-blue-50 border-l-4 border-blue-500 p-4">
              <h4 className="font-bold mb-2">Regras de Comissão:</h4>
              <ul className="space-y-1 text-sm">
                <li>• <strong>3%</strong>: Quando Preço de Venda = Preço de Tabela</li>
                <li>• <strong>4%</strong>: Quando Preço de Venda ≥ (Preço de Tabela + 6%)</li>
              </ul>
            </div>
          </div>
        )}

        {/* Módulo Inadimplência */}
        {activeModule === 'inadimplencia' && (
          <div>
            <h2 className="text-3xl font-bold mb-6">Módulo de Inadimplência</h2>
            
            <div className="bg-white p-6 rounded-lg shadow mb-6">
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Vendedor</label>
                  <select className="w-full px-3 py-2 border rounded-lg">
                    <option>Todos</option>
                    {[...new Set(inadimplencia.map(i => i['Funcionário']))].map(f => (
                      <option key={f}>{f}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Cliente</label>
                  <select className="w-full px-3 py-2 border rounded-lg">
                    <option>Todos</option>
                    {[...new Set(inadimplencia.map(i => i['Razão Social']))].map(r => (
                      <option key={r}>{r}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Ações</label>
                  <button
                    onClick={() => exportToCSV(inadimplencia, 'inadimplencia.csv')}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
                  >
                    <Download size={18} />
                    Exportar CSV
                  </button>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Documento</th>
                      <th className="px-4 py-2 text-left">Cliente</th>
                      <th className="px-4 py-2 text-left">Vendedor</th>
                      <th className="px-4 py-2 text-center">Vencimento</th>
                      <th className="px-4 py-2 text-right">Valor</th>
                      <th className="px-4 py-2 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {inadimplencia.map((item, i) => {
                      const vencimento = new Date(item['Dt.Vencimento']);
                      const hoje = new Date();
                      const diasAtraso = Math.floor((hoje - vencimento) / (1000 * 60 * 60 * 24));
                      const atrasado = diasAtraso > 0;

                      return (
                        <tr key={i} className="border-t hover:bg-gray-50">
                          <td className="px-4 py-3 font-mono">{item['No Doc']}</td>
                          <td className="px-4 py-3">{item['Razão Social']}</td>
                          <td className="px-4 py-3">{item['Funcionário']}</td>
                          <td className="px-4 py-3 text-center">
                            {new Date(item['Dt.Vencimento']).toLocaleDateString('pt-BR')}
                          </td>
                          <td className="px-4 py-3 text-right font-bold">
                            R$ {item['Vr.Líquido'].toLocaleString('pt-BR')}
                          </td>
                          <td className="px-4 py-3 text-center">
                            {atrasado ? (
                              <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
                                {diasAtraso} dias
                              </span>
                            ) : (
                              <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                                A vencer
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-500">
                <p className="font-bold">Total em Aberto: R$ {inadimplencia.reduce((acc, i) => acc + i['Vr.Líquido'], 0).toLocaleString('pt-BR')}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GestaoComercial;
