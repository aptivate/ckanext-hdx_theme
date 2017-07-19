DOWNLOADS_PER_DATASET = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id","properties.dataset id"],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(2)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      dataset_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

PAGEVIEWS_PER_DATASET = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "page view"}}]
  }})
  .groupBy(["properties.dataset id"],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      dataset_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

DOWNLOADS_PER_DATASET_PER_WEEK = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id","properties.dataset id",mixpanel.numeric_bucket('time',mixpanel.weekly_time_buckets)],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(2)}}],mixpanel.reducer.count())
  .sortAsc(function(row){{return row.key[1]}})
  .map(function(r){{
    return {{
      dataset_id: r.key[0],
      date: new Date(r.key[1]).toISOString().substring(0,10),
      value: r.value
    }};
  }});
}}
'''

PAGEVIEWS_PER_ORGANIZATION = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "page view"}}]
  }})
  .groupBy(["distinct_id","properties.org id"],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(1)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

DOWNLOADS_PER_ORGANIZATION = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.org id"],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(1)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

PAGEVIEWS_PER_ORGANIZATION_PER_WEEK = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "page view", selector: 'properties["org id"] != ""'}}]
  }})
  .groupBy(["properties.org id",mixpanel.numeric_bucket('time',mixpanel.weekly_time_buckets)],mixpanel.reducer.count())
  .sortAsc(function(row){{return row.key[1]}})
  .map(function(r){{
    return {{
      org_id: r.key[0],
      date: new Date(r.key[1]).toISOString().substring(0,10),
      value: r.value
    }};
  }});
}}
'''

DOWNLOADS_PER_ORGANIZATION_PER_WEEK = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id","properties.org id",mixpanel.numeric_bucket('time',mixpanel.weekly_time_buckets)],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(2)}}],mixpanel.reducer.count())
  .sortAsc(function(row){{return row.key[1]}})
  .map(function(r){{
    return {{
      org_id: r.key[0],
      date: new Date(r.key[1]).toISOString().substring(0,10),
      value: r.value
    }};
  }});
}}  
'''

DOWNLOADS_PER_ORGANIZATION_PER_DATASET = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets),"properties.dataset id", "properties.org id"],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(4)}}, function(row) {{return row.key.slice(3)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      dataset_id: r.key[1],
      value: r.value
    }};
  }})
  .sortDesc('value');
}}
'''