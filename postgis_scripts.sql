-- Euclidean distance between consecutive stops in same line and direction
select ligne, l.variante, s1.succession as stop, s1.descr_fr as stop, st_astext(s1.geom) as info,
		st_distance(s1.geom,s2.geom) as dist_next
from actu_stops s1
join actu_stops s2 on s1.code_ligne = s2.code_ligne and s1.variante = s2.variante
join actu_lines l on l.ligne = s1.code_ligne and l.variante = s1.variante
where s1.succession + 1 = s2.succession
group by ligne, l.variante, s1.succession, s1.descr_fr, s1.geom, s2.geom
order by ligne, l.variante, s1.succession;

-- Line length between consecutive stops in same line and direction
select ligne, l.variante, s1.stop_id as from, s1.descr_fr as from_descr_fr, s2.stop_id as to, s2.descr_fr as to_descr_fr,
	st_length(
		st_linesubstring(
			l.geom, st_linelocatepoint(st_linemerge(l.geom), s1.geom), st_linelocatepoint(st_linemerge(l.geom), s2.geom))) as dist
from actu_lines l
join actu_stops s1 on s1.code_ligne = l.ligne and s1.variante = l.variante
join actu_stops s2 on s2.code_ligne = l.ligne and s2.variante = l.variante
where s1.succession + 1 = s2.succession;
