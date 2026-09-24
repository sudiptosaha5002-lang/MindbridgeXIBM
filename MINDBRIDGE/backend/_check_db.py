import sqlite3
c = sqlite3.connect('mindbridge.db'); c.row_factory = sqlite3.Row
cols = [r[1] for r in c.execute('PRAGMA table_info(providers)')]
print('new cols:', [x for x in cols if x in ('phone', 'hospital_id', 'website_url', 'locality')])
print('total providers:', c.execute('SELECT COUNT(*) FROM providers').fetchone()[0])
print('unsplash left:', c.execute("SELECT COUNT(*) FROM providers WHERE avatar_url LIKE '%unsplash%'").fetchone()[0])
print('with phone:', c.execute('SELECT COUNT(*) FROM providers WHERE phone IS NOT NULL').fetchone()[0])
print('with hospital:', c.execute('SELECT COUNT(*) FROM providers WHERE hospital_id IS NOT NULL').fetchone()[0])
print('clinics:', c.execute('SELECT COUNT(*) FROM clinics').fetchone()[0])
print('narayana/apollo:', [r[0] for r in c.execute("SELECT id FROM clinics WHERE id IN ('clinic-narayana','clinic-apollo')")])
for r in c.execute("SELECT id, name, fee_per_session, phone, hospital_id, (avatar_url IS NULL) AS blank FROM providers WHERE id IN ('prov-psych-narayana','prov-psych-apollo','prov-psych-barasat')"):
    print(dict(r))
print('narayana doctors:', c.execute('SELECT COUNT(*) FROM providers WHERE is_verified=1 AND hospital_id=?', ('clinic-narayana',)).fetchone()[0])
print('apollo doctors:', c.execute('SELECT COUNT(*) FROM providers WHERE is_verified=1 AND hospital_id=?', ('clinic-apollo',)).fetchone()[0])
