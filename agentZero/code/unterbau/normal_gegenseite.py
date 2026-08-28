import vorprozessor as vp
c = vp._connect()
vp._ensure_vp_tables(c)
pk = vp.paket("gegenhypothese widerlegt superseded", conn=c)
print(pk["politik"]["nie_gekappt"])
c.close()
