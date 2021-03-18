function update_show_hist() {
  if (show_hist_cb.checked) {
    historyEl.style.display = 'block';
  } else {
    historyEl.style.display = 'none';
  }
}

function init() {
  if ('participants' in window.localStorage) {
    document.getElementById('participants').value = window.localStorage.participants;
  }
  if ('history' in window.localStorage) {
    document.getElementById('history').value = window.localStorage.history;
  }
  show_hist_cb = document.getElementById('show_hist');
  historyEl = document.getElementById('history');

  update_show_hist(); // reload might have it checked.
  show_hist_cb.addEventListener('input', update_show_hist);
}

window.onload = init;

function build_cost_matrix(participants, history) {
  cost_matrix = {}
  for (age = 0; age < history.length; ++age) {
    row = history[age]
    for (const table of row) {
      for (const person of table) {
        if (!participants.includes(person)) {
          continue
        }
        for (const qerson of table) {
          if (qerson == person) {
            break
          }
          if (!participants.includes(qerson)) {
            continue
          }
          match = person + '+' + qerson;
          if (qerson < person) {
            match = qerson + '+' + person;
          }
          incr = 1. / (1 << age);
          if (match in cost_matrix) {
            cost_matrix[match] += incr;
          } else {
            cost_matrix[match] = incr;
          }
        }
      }
    }
  }
  return cost_matrix
}


function cost_for_participant(person, tables, cost_matrix, max_persons_per_table)
{
  highest_table_cost = -1;
  min_cost = 10;
  min_cost_itable = null;
  for (itable = 0; itable < tables.length; ++itable) {
    table = tables[itable];
    if (table.length >= max_persons_per_table) {
      continue;
    }
    cost = 0
    for (const qerson of table) {
      match = person + '+' + qerson;
      if (qerson < person) {
        match = qerson + '+' + person;
      }
      if (match in cost_matrix) {
        cost += cost_matrix[match];
      }
    }
    // Vividly prefer or single-participant tables
    if (table.length < 2) {
      cost -= 1;
    }
    // Favor rather empty tables
    cost -= 0.5 / (1 + table.length);
    if (cost > highest_table_cost) {
      highest_table_cost = cost;
    }
    if (cost < min_cost) {
      min_cost = cost;
      min_cost_itable = itable;
    }
  }
  return [min_cost_itable, highest_table_cost];
}

// https://stackoverflow.com/questions/2450954/how-to-randomize-shuffle-a-javascript-array
function shuffle(array) {
  var currentIndex = array.length, temporaryValue, randomIndex;

  // While there remain elements to shuffle...
  while (0 !== currentIndex) {

    // Pick a remaining element...
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    // And swap it with the current element.
    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}

function distribute(cost_matrix, participants, max_persons_per_table)
{
  // Assign participants to tables, reducing the cost per participant.
  num_tables = Math.ceil(participants.length / max_persons_per_table);
  tables = new Array(num_tables).fill(0).map(el => new Array());
  shuffled_names = participants;
  shuffle(shuffled_names);
  tables[0].push(shuffled_names[0]);
  shuffled_names.splice(0, 1);

  // always pick the person with the highest potential table cost
  while (shuffled_names.length) {
    highest_cost = -100;
    highest_cost_name = null;
    highest_cost_name_min_cost_itable = -1;
    for (const person of shuffled_names) {
      [min_cost_itable, highest_table_cost] = cost_for_participant(
        person, tables, cost_matrix, max_persons_per_table);
      if (highest_table_cost > highest_cost) {
        highest_cost = highest_table_cost;
        highest_cost_name = person;
        highest_cost_name_min_cost_itable = min_cost_itable;
      }
    }
    tables[highest_cost_name_min_cost_itable].push(highest_cost_name);
    shuffled_names = shuffled_names.filter(name => name != highest_cost_name);
  }
  return tables;
}


function showTables(tables) {
  tableEl = document.getElementById('tables');
  while (tableEl.rows.length) {
    tableEl.deleteRow(0);
  }
  for (itable = 0; itable < tables.length; ++itable) {
    row = tableEl.insertRow();
    row.insertCell().innerText = `${itable + 1}`;
    row.insertCell().innerText = `${tables[itable].join(', ')}`;
  }
  document.getElementById('results').style.display = 'block';
}



/*
Generate tables that
- seat all participants, as imported from "names.py"
- minimize recent re-encounters
- have max_persons_per_table - which can be a float, defining the number of tables
- balance the number of participants per table
*/

function go() {
  hist = Array()
  histTxt = document.getElementById('history').value;
  dry_run = document.getElementById('dry_run').checked;
  retry = document.getElementById('retry').checked;
  if (histTxt.length) {
    hist = JSON.parse(histTxt);
    if (dry_run) {
      // Store what we have now; window.localStorage.history won't get modified later.
      window.localStorage.history = histTxt;
    }
  }
  participantsTxt = document.getElementById('participants').value;
  window.localStorage.participants = participantsTxt;
  names = participantsTxt.split('\n');
  names = names.map(name => name.trim()).filter(name => name.length > 0 && name[0] != '#');

  max_persons_per_table = Number(document.getElementById('perTable').value);

  // print(json.dumps(hist))
  cost_matrix = build_cost_matrix(names, hist);
  // print(json.dumps(cost_matrix))

  tables = distribute(cost_matrix, names, max_persons_per_table);
  for (itable = 0; itable < tables.length; ++itable) {
    console.log(`Table ${itable + 1}: ${tables[itable].join(', ')}`);
  }
  if (dry_run) {
    console.log('Dry-run mode; not storing distribution.')
  } else {
    if (hist.length && retry) {
      // replace newest one
      hist[0] = tables;
    } else {
      hist.splice(0, 0, tables);
    }
    if (hist.length > 6) {
      hist.slice(6); // drop last history entries
    }
    histJSON = JSON.stringify(hist);
    window.localStorage.history = histJSON;
    document.getElementById('history').value = histJSON;
  }
  showTables(tables);
  return false;
}