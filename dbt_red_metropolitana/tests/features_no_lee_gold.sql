-- Regla 2.3: la tabla de features sale de Silver, nunca de Gold.
-- Falla si el modelo de features depende de algún modelo del esquema gold.
{% set dependencias_gold = [] %}
{% if execute %}
    {% set nodo = graph.nodes['model.dbt_red_metropolitana.features_usuario_movilidad'] %}
    {% for dep in nodo.depends_on.nodes %}
        {% if dep in graph.nodes and graph.nodes[dep].schema == 'gold' %}
            {% do dependencias_gold.append(dep) %}
        {% endif %}
    {% endfor %}
{% endif %}

select '{{ dependencias_gold | join(", ") }}' as dependencia_prohibida
where {{ dependencias_gold | length }} > 0
