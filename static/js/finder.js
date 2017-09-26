;DSS.finder = {
  doQuery: function() {
    console.log('Running query');
    var data = {
      'reference_forms': $("#ref-area").val(),
      'reading_forms': $("#read-area").val(),
      'variant_forms': $("#var-area").val(),
      'name': $("#name-area").val(),
      'generated_id': DSS.finder.generated_id,
      'generated_name': DSS.finder.generated_name
    };
    var hasRefMSS = false;
    var checkboxes = $("input[type='checkbox']").filter(function() { return this.id.match(/refms/); })
    for (var i = 0; i < checkboxes.length; i++) {
      if (checkboxes[i].checked == true) {
        data['rms' + checkboxes[i].value] = 1;
        hasRefMSS = true;
      }
    }
    if (!hasRefMSS) {
      $('#messages').text('Please select a reference manuscript.');
      return;
    }
    document.getElementById('cblayerM').checked ? data['layer_M'] = 1 : data['layer_M'] = 0;
    document.getElementById('cblayerD').checked ? data['layer_D'] = 1 : data['layer_D'] = 0;
    document.getElementById('cblayerL').checked ? data['layer_L'] = 1 : data['layer_L'] = 0;
    document.getElementById('cbsave').checked ? data['save_query'] = 1 : data['save_query'] = 0;

    $('#query-button').prop("disabled",true);
    $('#messages').text('Please wait ...');
    $.ajax({url: '/app/query',
      data: data,
      success: function(response) {
        $('#messages').text('Done!');
        $('#query-button').prop("disabled", false);
        $('#content').empty();
        $('#content').html(response);

        $.ajax({url: '/app/startFinder',
          success: function(response) {
            $('#messages').text('Done!');
            $('#dirslist').empty();
            $('#dirslist').html(response);
          },
          error: function(xhr, status, error) {
            $('#messages').html('Error');
        }});
      },
      error: function(xhr, status, error) {
        $('#messages').html('Error');
    }});
  },
  selectCriteria: function(event) {
    var gen_id = '';
    var gen_name = '';
    var c_id = $('#finder-select option:selected').val().trim();
    var criteria = DSS.finder.queryBase.query_map[c_id];

    var ref_forms = criteria['reference_forms'];
    if (ref_forms) {
      gen_id = gen_id + '_REF';
      text_str = '';
      for (var i = 0; i < ref_forms.length; i++) {
        frm = ref_forms[i];
        if (text_str.length > 0) text_str = text_str + ',';
        text_str = text_str + frm;
        gen_id = gen_id + '_' + frm;
      }
      gen_name = gen_name + text_str;
      $("#ref-area").val(text_str);
    }
    else {
      $("#ref-area").val('');
    }

    var read_forms = criteria['reading_forms'];
    if (read_forms) {
      gen_id = gen_id + '_READ';
      text_str = '';
      for (var i = 0; i < read_forms.length; i++) {
        frm = read_forms[i];
        if (text_str.length > 0) text_str = text_str + ',';
        text_str = text_str + frm;
        gen_id = gen_id + '_' + frm;
      }
      if (text_str.length > 0) {
        if (gen_name.length > 0) {
          gen_name = gen_name + '; ';
        }
        gen_name = gen_name + 'R: ' + text_str;
      }
      $("#read-area").val(text_str);
    }
    else {
      $("#read-area").val('');
    }

    var var_forms = criteria['variant_forms'];
    if (var_forms) {
      gen_id = gen_id + '_VAR';
      text_str = '';
      for (var i = 0; i < var_forms.length; i++) {
        frm = var_forms[i];
        if (text_str.length > 0) text_str = text_str + ',';
        text_str = text_str + frm;
        gen_id = gen_id + '_' + frm;
      }
      if (text_str.length > 0) {
        if (gen_name.length > 0) {
          gen_name = gen_name + '; ';
        }
        gen_name = gen_name + 'V: ' + text_str;
      }
      $("#var-area").val(text_str);
    }
    else {
      $("#var-area").val('');
    }

    var layers = criteria['layers'];
    if (layers) {
      layers.indexOf('M') >= 0 ? document.getElementById('cblayerM').checked = true : document.getElementById('cblayerM').checked = false;
      layers.indexOf('D') >= 0 ? document.getElementById('cblayerD').checked = true : document.getElementById('cblayerD').checked = false;
      layers.indexOf('L') >= 0 ? document.getElementById('cblayerL').checked = true : document.getElementById('cblayerL').checked = false;
    }

    $("#name-area").val(criteria['generated_name']);

    DSS.finder.generated_id = gen_id;
    DSS.finder.generated_name = gen_name;

    console.log('generated id:', gen_id);
    console.log('generated name:', gen_name);
  },
  selectResult: function(event) {
    console.log('Fetching saved result');
    var c_id = $('#results-select option:selected').val().trim();
    var data = {
      'result_id': c_id
    };
    $.ajax({url: '/app/fetchresult',
      data: data,
      success: function(response) {
        $('#messages').text('Done!');
        $('#content').empty();
        $('#content').html(response);
      },
      error: function(xhr, status, error) {
        $('#messages').html('Error');
    }});
 }
}