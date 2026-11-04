export function dbError(e) {
  if (e.code === 'ER_DUP_ENTRY') return Response.json({ error: 'Duplicate entry: ' + e.sqlMessage }, { status: 409 });
  if (e.code === 'ER_ROW_IS_REFERENCED_2') return Response.json({ error: 'Cannot delete: record is referenced by other records (e.g. citations)' }, { status: 409 });
  if (e.sqlState === '45000' || e.code === 'ER_CHECK_CONSTRAINT_VIOLATED' || e.code === 'ER_NO_REFERENCED_ROW_2')
    return Response.json({ error: e.sqlMessage }, { status: 400 });
  console.error(e);
  return Response.json({ error: 'Server error' }, { status: 500 });
}
export const bad = (msg) => Response.json({ error: msg }, { status: 400 });
export const isDate = (s) => /^\d{4}-\d{2}-\d{2}$/.test(s) && !isNaN(new Date(s));
