export default function DataTable({ data }) {
  if (!data?.length) return (
    <p className="text-xs text-smoke/40 text-center py-8">Sin resultados</p>
  )

  const columns = Object.keys(data[0])

  return (
    <div className="overflow-x-auto scrollbar-thin rounded-lg border border-white/10">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-white/10 bg-white/5">
            {columns.map(col => (
              <th key={col} className="px-3 py-2 text-left text-smoke/50 font-semibold uppercase tracking-wider whitespace-nowrap">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
              {columns.map(col => (
                <td key={col} className="px-3 py-2 text-smoke/80 whitespace-nowrap">
                  {row[col] ?? '—'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
