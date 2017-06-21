;DSS = {
  name: 'DSS',
  buildObjects: function() { // name hard-coded in html!
    DSS.model = DSS.models[0];
    DSS.chapter = new DSS.Chapter();
  },
  buildDOM: function() {
    var table = $('<table>');
    $("#divMain").html(table);

    var NUM_ROWS = DSS.chapter.maxForms * 2 + DSS.chapter.headerRows + DSS.chapter.varUnitRows;
    var rows = [];
    var tr;
    for (var rowIdx = 0; rowIdx < NUM_ROWS; rowIdx++) {
      // Header row
      if (rowIdx == 0) {
        tr = $('<tr>');
      }
      // Rows for variation units
      else if (rowIdx >= DSS.chapter.headerRows && rowIdx < DSS.chapter.headerRows + DSS.chapter.varUnitRows) {
        tr = $('<tr>', {class:'row-variation'});
      }
      // Rows for text forms
      else if (rowIdx >= DSS.chapter.headerRows + DSS.chapter.varUnitRows && rowIdx < DSS.chapter.headerRows + DSS.chapter.varUnitRows + DSS.chapter.maxForms) {
        var rowClass = 'row-even';
        if (rowIdx === 1) {
          rowClass = 'row-bezae';
        }
        else if ((rowIdx + 1) % 2 === 1) {
          rowClass = 'row-odd';
        }
        tr = $('<tr>', {class:rowClass});
      }
      // Remaining rows for text form work area
      else {
        tr = $('<tr>');
      }
      table.append(tr);
      rows.push(tr);
    }

    // Row contents by column
    for (var slotIdx = 0; slotIdx < DSS.chapter.addresses.length; slotIdx++) {
      var slot = DSS.chapter.addresses[slotIdx];
      var value = '';
      var handler;
      var tr, td;

      // Verse
      if (slot.type === 'verse') {
        for (var rowIdx = 0; rowIdx < NUM_ROWS; rowIdx++) {
          tr = rows[rowIdx];
          value = slot.verseNum;
          td = $('<td>', {text:value});
          if (rowIdx === 0) {
            td.addClass('button');
          }
          if (rowIdx < DSS.chapter.maxForms + 1) {
            td.addClass('textRegion');
          }
          tr.append(td);
        }
        continue;
      }

      // Header
      var tr = rows[0];
      td = $('<td>');
      tr.append(td);
      slot.headerCell = td;

      // Variant area
      for (var rowIdx = DSS.chapter.headerRows; rowIdx < DSS.chapter.headerRows + DSS.chapter.varUnitRows; rowIdx++) {
        tr = rows[rowIdx];
        var td = $('<td>');
        td.addClass('textRegion');
        tr.append(td);
        slot.varUnitCells.push(td);
      }

      // Text forms
      for (var rowIdx = DSS.chapter.headerRows + DSS.chapter.varUnitRows; rowIdx < DSS.chapter.headerRows + DSS.chapter.varUnitRows + DSS.chapter.maxForms; rowIdx++) {
        tr = rows[rowIdx];
        var td = $('<td>');
        td.addClass('textRegion');
        tr.append(td);
        slot.textCells.push(td);
      }

      // Work area
      for (var rowIdx = DSS.chapter.headerRows + DSS.chapter.varUnitRows + DSS.chapter.maxForms; rowIdx < NUM_ROWS; rowIdx++) {
        tr = rows[rowIdx];
        td = $('<td>');
        tr.append(td);
        slot.workCells.push(td);
      }
      slot.refresh();
    }

    // Keyboard events for file operations
    $(window).keydown(function(event){
      if (event.altKey && event.keyCode === 83) { // S = Save diffs
        //DSS.Chapter.handleSave.call(DSS.chapter, event);
        DSS.Chapter.handleSaveDiffs.call(DSS.chapter, event);
      }
      else if (event.altKey && event.keyCode === 79) { // O = Open diffs
        //DSS.Chapter.handleOpen.call(DSS.chapter, event);
        DSS.Chapter.handleOpenDiffs.call(DSS.chapter, event);
      }
      else if (event.altKey && event.keyCode === 77) { // M = Toggle morphology
        // Open model diffs
        DSS.Chapter.handleToggleMorphology.call(DSS.chapter, event);
      }
      else if (event.altKey && event.keyCode === 65) { // A = Save all
        DSS.Chapter.handleSaveAll.call(DSS.chapter, event);
      }
    });

    // File open
    $('#inputFilePart').bind('change', DSS.Chapter.handleLoadDiffs.bind(DSS.chapter));
  }
}