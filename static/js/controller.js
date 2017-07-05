;DSS = {
  clustAnalyze: function() {
    DSS.analyze('clustanalyze')
  },
  boolAnalyze: function() {
    DSS.analyze('boolanalyze')
  },
  analyze: function(action) {
    var inputfile = $('#inputfile').val();
    var chapter = $('#inputfile option:selected').text().trim();
    var data = {
        'inputfile': inputfile,
        'chapter': chapter
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
      return;
    }

    $("#canalyze").addClass('disable-link');
    $("#banalyze").addClass('disable-link');
    $('#messages').text('Please wait ...');

    $.ajax({url: '/app/' + action,
      data: data,
      success: function(response) {
        $('#messages').text('Done!');
        $("#canalyze").removeClass('disable-link');
        $("#banalyze").removeClass('disable-link');

        $('#dirslist').empty();
        $('#dirslist').html(response);
      },
      error: function(xhr, status, error) {
        $('#messages').html('Error');
        $("#canalyze").removeClass('disable-link');
        $("#banalyze").removeClass('disable-link');
    }});
  },
  accordionClick: function(event) {
    var target = $(event.target);
    $('.accordion-body').addClass('accordion-hidden');
    target.next().removeClass('accordion-hidden');
  },
  chFromDir: function(dir) {
    return dir.replace(/Mark (\d{2,2})\-\d{1,4}[GL]{1,2}/gi, '$1');
  },
  msFromDir: function(dir) {
    return dir.replace(/Mark \d{2,2}\-(\d{1,4})[GL]{1,2}/gi, '$1');
  },
  stripLangCode: function(dir) {
    return dir.replace(/(Mark \d{2,2}\-\d{1,4})[GL]{1,2}/gi, '$1');
  },
  viewClusterPlot: function(dir, subdir, filename, title, isGL) {
    $('#content').empty();
    // e.g. Mark 01-01GL
    var ms = DSS.msFromDir(dir);
    var ch = DSS.chFromDir(dir);
    var langCode = isGL ? 'GL' : 'G';
    var div = $('<div>', {text: 'MS ' + ms + ' ' + langCode + ' Chapter ' + ch + ' - ' + subdir + ' ' + title, class: 'ms-heading'});
    $('#content').append(div);
    var img = $('<img>', {src: 'static/stats/' + dir + '/' + subdir + ' clusters/' + dir + ' - ' + subdir + ' ' + filename + '.png'});
    $('#content').append(img);
  },
  viewGraphic: function(dir, subfolder, filename, title) {
    $('#content').empty();
    // e.g. Mark 01-01GL
    var ms = DSS.msFromDir(dir);
    var ch = DSS.chFromDir(dir);
    var div = $('<div>', {text: 'MS ' + ms + ' - Chapter ' + ch + ' - ' + title, class: 'ms-heading'});
    $('#content').append(div);
    // e.g. Mark 01-01GL - 4 clusters by Latin Witness
    var img = $('<img>', {src: 'static/stats/' + dir + '/' + subfolder + '/' + dir + ' - ' + filename + '.png'});
    $('#content').append(img);
  },
  viewClusterResults: function(dir, subdir, action) {
    $.ajax({url: '/static/stats/' + dir + '/' + subdir + ' clusters/' + dir + '-' + subdir + 'cl-results.json',
      success: function(response) {
        $.post({url: '/app/' + action,
        data: {
          'json': response
        },
        success: function(response) {
          $('#content').html(response);
          $('#messages').text('Done!');
        },
        error: function(xhr, status, error) {
          $('#messages').html('Error');
        }});
      },
      error: function(xhr, status, error) {
        $('#messages').html('Error');
    }});
  },
  viewClusterMerge: function(dir, action) {
    // dir = Mark 01-05GL
    $.ajax({url: '/static/layers/' + DSS.stripLangCode(dir) + '.json',
      success: function(response) {
        $.post({url: '/app/' + action,
        data: {
          'json': response
        },
        success: function(response) {
          $('#content').html(response);
          $('#messages').text('Done!');
        },
        error: function(xhr, status, error) {
          $('#messages').html('Error');
        }});
      },
      error: function(xhr, status, error) {
        $('#messages').html('Error');
    }});
  },
  viewQCA: function(dir, filebase) {
    $('#content').empty();
    $.ajax({url: '/static/stats/' + dir + '/' + filebase + '-header.html',
      async: false,
      success: function(response) {
        $('#content').append(response);
        $('#messages').text('Done!');
      },
      error: function(xhr, status, error) {
        $('#messages').html('Error');
      }});
    $.ajax({url: '/static/stats/' + dir + '/' + filebase + '.html',
      success: function(response) {
        $('#content').append(response);
        $('#messages').text('Done!');
      },
      error: function(xhr, status, error) {
        $('#messages').html('Error');
      }});
  }
}