-- Euclidean distance between consecutive stops in same line and direction
select ligne, l.variante, s1.succession as stop, s1.descr_fr as stop, st_astext(s1.geom) as info,
		st_distance(s1.geom,s2.geom) as dist_next
from actu_stops s1
join actu_stops s2 on s1.code_ligne = s2.code_ligne and s1.variante = s2.variante
join actu_lines l on l.ligne = s1.code_ligne and l.variante = s1.variante
where s1.succession + 1 = s2.succession
group by ligne, l.variante, s1.succession, s1.descr_fr, s1.geom, s2.geom
order by ligne, l.variante, s1.succession;

-- Here we assign to each line and direction the collection of stops
-- 	the idea is to now divide the line using these points and
-- 	compute the length of each segment
select ligne, l.variante, st_astext(st_collect(s1.geom))
from actu_lines l 
join actu_stops s1 on s1.code_ligne = l.ligne
group by ligne, l.variante
order by ligne;
