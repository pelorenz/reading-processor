DSS.Chapter = function () {
  this.morphOn = false;
  this.headerRows = 1;
  this.varUnitRows = 3;
  this.maxForms = 0;
  this.manuscripts = [];
  this.addresses = [];
  this.addressLookup = {};
  this.filename = DSS.models[0]._filename;
  this.chapterNum = DSS.models[0].chapter;
  for (var i = 0; i < DSS.models.length; i++) {
    var model = DSS.models[i];
    this.manuscripts = this.manuscripts.concat(model.manuscripts);
    for (var j = 0; j < model.addresses.length; j++) {
      var slot = model.addresses[j];
      if (slot._type == 'verse') {
        if (j >= this.addresses.length) { // new tokens only!
          var vDelim = new DSS.VerseDelimiter(slot.tokenIndex, slot.verse);
          this.addresses.push(vDelim);
        }
      }
      else if (slot._type == 'address') {
        if (j >= this.addresses.length) { // add new slots only!
          var addr = new DSS.Address(j, this.chapterNum, slot.verse, slot.addressIndex, slot.textForms); // reset token index to actual order (i.e. j)
          this.addresses.push(addr);
          this.addressLookup[slot.verse + ':' + slot.addressIndex] = addr;
        }
        else {
          addr = this.getAddress(slot['verse'], slot['addressIndex'])
          addr.appendTextForms(slot.textForms);
        }
        if (addr.textForms.length > this.maxForms) {
          this.maxForms = addr.textForms.length;
        }
      }
    }
  }
};
DSS.Chapter.prototype.getAddress = function (verse, addrIdx) {
  var key = verse + ':' + addrIdx;
  if (key in this.addressLookup) {
    return this.addressLookup[key];
  }
  return undefined;
};
DSS.Chapter.handleToggleMorphology = function (event) {
  if (DSS.chapter.morphOn == true) {
    DSS.chapter.morphOn = false;
    $('.morph_on').attr('class', 'morph_off')
  }
  else {
    DSS.chapter.morphOn = true;
    $('.morph_off').attr('class', 'morph_on')
  }
};
DSS.Chapter.handleOpenDiffs = function (event) {
  $("#inputFilePart").click();
};
DSS.Chapter.handleLoadDiffs = function (event) {
  var file = event.target.files[0];
  var reader = new FileReader();
  reader.onload = DSS.Chapter.processUploadDiffs.bind(DSS.chapter);
  reader.readAsText(file);
};
DSS.Chapter.processUploadDiffs = function (event) {
  console.log('Loading model diffs');
  var content = event.target.result;
  DSS.modelDiff = [];
  DSS.modelDiff = JSON.parse(content);

  // Confirm that models derive from same file
  if (DSS.modelDiff['_filename'] == this.filename) {
    for (var i = 0; i < DSS.modelDiff['addresses'].length; i++) {
      // Iterate addresses in diff file
      var j_addr = DSS.modelDiff['addresses'][i];
      var addr = DSS.chapter.getAddress(j_addr['verse'], j_addr['addressIndex']);
      if (!addr) {
        continue;
      }

      // Remove groups and variation units to prepare to reload
      addr.clearGroups();
      addr.variationUnits = [];

      // Iterate text forms in diff file
      for (var j = 0; j < j_addr['textForms'].length; j++) {
        var j_form = j_addr['textForms'][j];
        var group = new DSS.TextFormGroup();

        // Iterate grouped text forms in diff file
        for (var k = 0; k < j_form['textForms'].length; k++) {
          var j_subform = j_form['textForms'][k];

          // Locate corresponding text form in current model
          for (var m = 0; m < addr.textForms.length; m++) {
            var frm = addr.textForms[m];
            if (frm.form == j_subform['form']) {
              addr.textForms.splice(m, 1);
              if (frm.form == j_form['mainForm']) {
                group.addTextForm(frm, true);
              }
              else {
                group.addTextForm(frm, false);
              }
              break;
            }
          }
        }
        addr.textForms.push(group);
      }
      for (var j = 0; j < j_addr['variationUnits'].length; j++) {
        var j_varunit = j_addr['variationUnits'][j];
        var short_label = '';
        var long_label = '';
        var j_label = j_varunit['label'];
        var is_long = j_label.match(/^\d{1,2}\.(\d{1,2}\..+)$/);
        if (is_long) {
          short_label = is_long.length > 1 ? is_long[1] : j_label;
          long_label = j_label;
        }
        else {
          short_label = j_label;
          long_label = this.chapterNum + '.' + j_label;
        }
        if (!addr.hasVariationUnit(short_label) && !addr.hasVariationUnit(long_label)) {
          var vu = new DSS.VariationUnit();
          vu.label = long_label;
          vu.hasRetroversion = j_varunit['hasRetroversion'];
          for (var k = 0; k < j_varunit['readings'].length; k++) {
            var j_reading = j_varunit['readings'][k];
            if (j_reading['_type'] == 'readingGroup') {
              var readingGroup = new DSS.ReadingGroup();
              readingGroup.displayValue = j_reading['displayValue'];
              for (var m = 0; m < j_reading['readings'].length; m++) {
                var j_subreading = j_reading['readings'][m];
                var subreading = new DSS.Reading();
                for (var n = 0; n < j_subreading['readingUnits'].length; n++) {
                  var j_ru = j_subreading['readingUnits'][n];
                  var ru = new DSS.ReadingUnit(j_ru['tokenIndex'], this.chapterNum, j_ru['verse'], j_ru['addressIndex'], j_ru['text']);
                  subreading.readingUnits.push(ru);
                  vu.addresses.push(DSS.chapter.getAddress(j_ru['verse'], j_ru['addressIndex']));
                }
                subreading.displayValue = j_subreading['displayValue'];
                subreading.manuscripts = j_subreading['manuscripts'];
                readingGroup.addReading(subreading);
              }
              readingGroup.manuscripts = j_reading['manuscripts'];
              vu.readings.push(readingGroup);
            }
            else {
              var reading = new DSS.Reading();
              for (var m = 0; m < j_reading['readingUnits'].length; m++) {
                var j_ru = j_reading['readingUnits'][m];
                var ru = new DSS.ReadingUnit(j_ru['tokenIndex'], this.chapterNum, j_ru['verse'], j_ru['addressIndex'], j_ru['text']);
                reading.readingUnits.push(ru);
                vu.addresses.push(DSS.chapter.getAddress(j_ru['verse'], j_ru['addressIndex']));
              }
              reading.displayValue = j_reading['displayValue'];
              reading.manuscripts = j_reading['manuscripts'];
              vu.readings.push(reading);
            }
          }
          addr.variationUnits.push(vu);
        }
      }
      addr.refresh();
    }
  }
  $('#inputFilePart').remove();
  var input = $('<input>', {type: 'file', id: 'inputFilePart'});
  input.css('display', 'none');
  $('body').prepend(input);
  $("#inputFilePart").bind('change', DSS.Chapter.handleLoadDiffs.bind(DSS.chapter));
};
DSS.Chapter.saveJSON = function(jsonString, isDiff) {
  var blob = new Blob(['\ufeff', jsonString], {type: 'text/json'});
  var e = document.createEvent('MouseEvents');
  var a = document.createElement('a');

  if (isDiff) {
    a.download = DSS.chapter.filename + '-diff.json';
  }
  else {
    a.download = DSS.chapter.filename + '-all.json';
  }
  a.href = window.URL.createObjectURL(blob);
  a.dataset.downloadurl =  ['text/json', a.download, a.href].join(':');
  e.initMouseEvent('click', true, false, window, 0, 0, 0, 0, 0, false, false, false, false, 0, null);
  a.dispatchEvent(e);
};
DSS.Chapter.handleSaveAll = function (event) {
  console.log('Saving model addresses');
  DSS.Chapter.handleSave.call(this, event, false);
};
DSS.Chapter.handleSaveDiffs = function (event) {
  console.log('Saving model diffs');
  DSS.Chapter.handleSave.call(this, event, true);
};
DSS.Chapter.handleSave = function (event, isDiff) {
  var saveModel = {
    '_filename': this.filename,
    'chapter': this.chapterNum,
    'addresses': []
  };
  if (!isDiff) {
    var sortedMSS = this.manuscripts;
    sortedMSS.sort(DSS.TextFormGroup.sortMSS);
    saveModel['manuscripts'] = sortedMSS;
  }
  for (var i = 0; i < this.addresses.length; i++) {
    var address = this.addresses[i];
    if (address.type == 'address') {
      var j_addr = {
        '_type': address.type,
        'tokenIndex': address.tokenIdx,
        'chapter': address.chapterNum,
        'verse': address.verseNum,
        'addressIndex': address.addressIdx,
        'textForms': [],
        'variationUnits': []
      };
      for (var j = 0; j < address.textForms.length; j++) {
        var frm = address.textForms[j];
        if (frm.type == 'textFormGroup') {
          var j_form = {
            '_type': 'textFormGroup',
            'mainForm': frm.mainForm,
            'textForms': []
          };
          for (var k = 0; k < frm.textForms.length; k++) {
            var subForm = frm.textForms[k];
            var j_subform = {
              '_type': 'textForm',
              'form': subForm.form
            }
            if (!isDiff) {
              j_subform['language'] = subForm.language;
              j_subform['linkedManuscripts'] = subForm.linkedMSS;
            }
            j_form['textForms'].push(j_subform);
          };
          if (j_form['textForms'].length > 0) {
            if (!j_form['mainForm']) {
              j_form['mainForm'] = j_form['textForms'][0]['form'];
            }
            j_addr['textForms'].push(j_form);
          }
        }
        else if (!isDiff && frm.type == 'form') {
          var j_form = {
            '_type': 'textForm',
            'form': frm.form,
            'language': frm.language,
            'linkedManuscripts': frm.linkedMSS
          }
          j_addr['textForms'].push(j_form);
        }
      }
      for (var j = 0; j < address.variationUnits.length; j++) {
        var vu = address.variationUnits[j];
        var j_varunit = {
          '_type': vu.type,
          'label': vu.label,
          'hasRetroversion': vu.hasRetroversion,
          'readings': []
        };
        for (var k = 0; k < vu.readings.length; k++) {
          var reading = vu.readings[k];
          if (reading.type == 'readingGroup') {
            var j_rgroup = {
              '_type': reading.type,
              'displayValue': reading.displayValue,
              'manuscripts': reading.manuscripts,
              'readings': []
            };
            for (var m = 0; m < reading.readings.length; m++) {
              var subrdg = reading.readings[m];
              var j_reading = {
                '_type': subrdg.type,
                'displayValue': subrdg.displayValue,
                'manuscripts': subrdg.manuscripts,
                'readingUnits': []
              };
              for (var n = 0; n < subrdg.readingUnits.length; n++) {
                var ru = subrdg.readingUnits[n];
                var j_ru = {
                  '_type': ru.type,
                  'tokenIndex': ru.tokenIdx,
                  'chapter': ru.chapterNum,
                  'verse': ru.verseNum,
                  'addressIndex': ru.addressIdx,
                  'text': ru.text
                };
                j_reading['readingUnits'].push(j_ru);
              }
              j_rgroup['readings'].push(j_reading);
            }
            j_varunit['readings'].push(j_rgroup);
          }
          else {
            var j_reading = {
              '_type': reading.type,
              'displayValue': reading.displayValue,
              'manuscripts': reading.manuscripts,
              'readingUnits': []
            };
            for (var m = 0; m < reading.readingUnits.length; m++) {
              var ru = reading.readingUnits[m];
              var j_ru = {
                '_type': ru.type,
                'tokenIndex': ru.tokenIdx,
                'chapter': ru.chapterNum,
                'verse': ru.verseNum,
                'addressIndex': ru.addressIdx,
                'text': ru.text
              };
              j_reading['readingUnits'].push(j_ru);
            }
            j_varunit['readings'].push(j_reading);
          }
        }
        j_addr['variationUnits'].push(j_varunit);
      }
      if (isDiff) {
        if (j_addr['textForms'].length > 0 || j_addr['variationUnits'].length > 0) {
          saveModel['addresses'].push(j_addr);
        }
      }
      else { // save all addresses
        saveModel['addresses'].push(j_addr);
      }
    }
  }
  var jsonString = JSON.stringify(saveModel);
  DSS.Chapter.saveJSON(jsonString, isDiff);
};

DSS.AddressSlot = function (t_idx, c_num, v_num) {
  this.tokenIdx = t_idx;
  this.chapterNum = c_num;
  this.verseNum = v_num;
};

DSS.Address = function (t_idx, c_num, v_num, a_idx, t_forms) {
  DSS.AddressSlot.call(this, t_idx, c_num, v_num);
  this.addressIdx = a_idx;
  this.type = 'address';
  this.manuscriptForms = {};
  this.textForms = [];
  this.variationUnits = [];

  this.appendTextForms(t_forms);

  // JQuery DOM elements
  this.headerCell = undefined;
  this.varUnitCells = [];
  this.textCells = [];
  this.workCells = [];
  this.checkbox = undefined;
};
DSS.Address.constructor = DSS.Address;
DSS.Address.prototype = Object.create(DSS.AddressSlot.prototype);

DSS.Address.handleClick = function () {
  if (this.checkbox.is(':checked')) { // address checkbox checked
    var vu = new DSS.VariationUnit();
    var t_idx = this.tokenIdx;
    var startingVerse = this.verseNum;
    var addresses = [];
    var addr = this;
    while (addr && startingVerse <= addr.verseNum + 2 && t_idx < DSS.chapter.addresses.length) {
      if (!addr.checkbox) { // verse headers
        t_idx++;
        addr = DSS.chapter.addresses[t_idx];
        continue;
      }
      if (addr.checkbox.is(':checked')) {
        addresses.push(addr);
        addr.checkbox.prop('checked', false); // not working?
      }
      t_idx++;
      addr = DSS.chapter.addresses[t_idx];
    }
    vu.initialize(addresses);
    this.variationUnits.push(vu);
    this.refresh();
  }
  else { // text form checkboxes checked
    var numChecked = 0;
    for (var i = this.textForms.length - 1; i >= 0; i--) {
      var frm = this.textForms[i];
      if (frm.checkbox.is(':checked')) {
        numChecked++;
      }
    }
    if (numChecked < 2) {
      return;
    }

    // Proceed if two or more elements checked
    var group = new DSS.TextFormGroup();
    for (var i = this.textForms.length - 1; i >= 0; i--) {
      var frm = this.textForms[i];
      if (!frm.checkbox) {
        continue;
      }
      if (frm.checkbox.is(':checked')) {
        this.textForms.splice(i, 1);
        group.addTextForm(frm, true);
      }
    }
    this.textForms.push(group);
    this.refresh();
    console.log(this.type + ' ' + this.verseNum.toString() + '.' + this.addressIdx.toString() + ':' + group.textForms.join(' '));
  }
};
DSS.Address.sortTextForms = function (frm1, frm2) {
  if (frm1.hasLinkedMS('05')) {
    return -1;
  }
  else if (frm2.hasLinkedMS('05')) {
    return 1;
  }

  if (frm1.language == 'greek' && frm2.language == 'latin') {
    return -1;
  }
  else if (frm1.language == 'latin' && frm2.language == 'greek') {
    return 1;
  }
  else if (frm1.linkedMSSCount() > frm2.linkedMSSCount()) {
    return -1;
  }
  else if (frm1.linkedMSSCount() < frm2.linkedMSSCount()) {
    return 1;
  }
  else {
    return 0;
  }
};
DSS.Address.prototype.refresh = function() {
  // Resort text forms
  this.textForms.sort(DSS.Address.sortTextForms);

  // Clean current cells
  var cleanCell = function (td) {
    td.empty();
    td.attr('class', '');
    td.attr('title', '');
  };
  var td;
  cleanCell(this.headerCell);
  for (var i = 0; i < this.varUnitCells.length; i++) {
    td = this.varUnitCells[i];
    cleanCell(td);
  }
  for (var i = 0; i < this.textCells.length; i++) {
    td = this.textCells[i];
    cleanCell(td);
  }
  for (var i = 0; i < this.workCells.length; i++) {
    td = this.workCells[i];
    cleanCell(td);
  }

  // Populate header
  var handler = DSS.Address.handleClick;
  this.headerCell.bind('click', handler.bind(this));
  var cb = $('<input>', {type:'checkbox'});
  cb.click(function(event){
    event.stopPropagation();
  });
  this.checkbox = cb;
  this.headerCell.addClass('button');
  this.headerCell.append(cb);
  this.headerCell.append(this.verseNum + '.' + this.addressIdx);

  // Populate variant units
  for (var i = 0; i < this.variationUnits.length; i++) {
    var varunit = this.variationUnits[i];
    varunit.render(this.varUnitCells[i]);
    handler = DSS.VariationUnit.handleCheck;
    varunit.checkbox.bind('click', handler.bind(varunit, this));
  }

  // Populate work area
  var workIdx = 0;
  for (var rowIdx = 0; rowIdx < DSS.chapter.maxForms; rowIdx++) {
    var td = this.textCells[rowIdx];
    td.addClass('textRegion');
    if (rowIdx < this.textForms.length) {
      var frm = this.textForms[rowIdx];
      this.initCell(frm, td);

      // Group
      if (frm.type == 'textFormGroup') {
        //frm.textForms.sort(DSS.Address.sortTextForms);
        var subFrm;
        for (var sfIdx = 0; sfIdx < frm.textForms.length; sfIdx++) {
          subFrm = frm.textForms[sfIdx];
          td = this.workCells[workIdx];
          this.initCell(subFrm, td);
          if (sfIdx == 0) {
            td.addClass('borderTop');
          }
          if (sfIdx == frm.textForms.length - 1) {
            td.addClass('borderBottom');
          }
          td.addClass('borderSides');
          td.addClass('workButton');
          if (subFrm.form == frm.mainForm) {
            td.addClass('mainForm');
          }
          handler = DSS.TextFormGroup.handleCheck;
          subFrm.checkbox.bind('click', handler.bind(frm, subFrm, this));

          handler = DSS.TextFormGroup.handleClick;
          td.bind('click', handler.bind(frm, subFrm, this));

          workIdx++;
        }
      }
    }
  }

  // Build MSS hash table
  this.manuscriptForms = {};
  for (var i = 0; i < DSS.chapter.manuscripts.length; i++) {
    var ms = DSS.chapter.manuscripts[i];
    for (var j = 0; j < this.textForms.length; j++) {
      var frm = this.textForms[j];
      if (frm.hasLinkedMS(ms)) {
        this.manuscriptForms[ms] = frm;
        break;
      }
    }
  }
};
DSS.Address.prototype.initCell = function(frm, td) {
  var title = frm.getMorph() + '\n' + frm.getLemma() + '\n' + frm.getLinkedMSS().join(' ');
  td.attr('title', title);
  if (frm.linkedMSSCount() == 1) {
    td.addClass('singular');
  }
  if (frm.hasLinkedMS('05') || frm.hasLinkedMS('VL5')) {
    td.addClass('cell-bezae');
  }
  if (frm.hasLinkedMS('35')) {
    td.addClass('cell-mainstream');
  }
  var cb = $('<input>', {type:'checkbox'});
  cb.click(function(event){
    event.stopPropagation();
  });
  frm.checkbox = cb;
  morphtxt = ''
  if (frm.getMorph()) {
    morphtxt = '(' + frm.getMorph() + ')';
  }
  var span = $('<span>', {class: 'morph_off', text: morphtxt, title: frm.getLemma()});
  if (DSS.chapter.morphOn == true) {
    span.attr('class', 'morph_on');
  }
  td.append([cb, frm.getForm(), span]);
};
DSS.Address.prototype.hasLinkedMS = function(id) {
  for (var i = 0; i < this.textForms.length; i++) {
    var frm = this.textForms[i];
    if (frm.hasLinkedMS(id)) {
      return true;
    }
  }
  return false;
};
DSS.Address.prototype.hasVariationUnit = function(label) {
  for (var i = 0; i < this.variationUnits.length; i++) {
    var vu = this.variationUnits[i];
    if (vu.label == label) {
      return true;
    }
    return false;
  }
};
DSS.Address.prototype.appendTextForms = function(t_forms) {
  for (var i = 0; i < t_forms.length; i++) {
    t_form = t_forms[i];
    if (t_form['_type'] == 'textFormGroup') {
      var tfGroup = new DSS.TextFormGroup();
      tfGroup.mainForm = t_form['mainForm'];
      for (var j = 0; j < t_form.textForms.length; j++) {
        var subform = t_form.textForms[j];
        var tForm = new DSS.TextForm(subform.form, subform.language, subform.linkedManuscripts, subform.morph, subform.lemma);
        tfGroup.textForms.push(tForm);
      }
      tfGroup.sortMSS();
      this.textForms.push(tfGroup);
    }
    else {
      if (t_form.form == 'om.') {
        var tForm = undefined;
        for (var j = 0; j < this.textForms.length; j++) {
          var tf = this.textForms[j];
          if (tf.form == 'om.') {
            tForm = tf;
            break;
          }
        }
        if (tForm) { // om. form already in list
          tForm.language = 'greek'; // greek overrides latin!
          tForm.linkedMSS = tForm.linkedMSS.concat(t_form.linkedManuscripts);
          tForm.linkedMSS.sort(DSS.TextFormGroup.sortMSS);
          continue; // fall through if om. not found
        }
      }
      if (t_form.form != '~' && t_form.form != '-') {
        var tForm = new DSS.TextForm(t_form.form, t_form.language, t_form.linkedManuscripts, t_form.morph, t_form.lemma);
        this.textForms.push(tForm);
      }
    }
  }
};
DSS.Address.prototype.clearGroups = function() {
  var textForms = [];
  for (var i = this.textForms.length - 1; i >= 0; i--) {
    var frm = this.textForms[i];
    if (frm.type == 'textFormGroup') {
      for (var j = 0; j < frm.textForms.length; j++) {
        var tf = frm.textForms[j];
        textForms.push(tf);
      }
    }
    else {
      textForms.push(frm);
    }
  }
  this.textForms = textForms;
};

DSS.VerseDelimiter = function (t_idx, c_num, v_num) {
  DSS.AddressSlot.call(this, t_idx, c_num, v_num);
  this.type = 'verse';
};
DSS.VerseDelimiter.constructor = DSS.VerseDelimiter;
DSS.VerseDelimiter.prototype = Object.create(DSS.AddressSlot.prototype);

DSS.VerseDelimiter.handleClick = function () {
  console.log(this.type + ' ' + this.verseNum.toString());
};

DSS.FormBase = function (mph, lem) {
  this.morph = mph;
  this.lemma = lem;
};
DSS.FormBase.prototype.getMorph = function(){
  return this.morph;
}
DSS.FormBase.prototype.getLemma = function(){
  return this.lemma;
}

DSS.TextForm = function (frm, lang, lnk_mss, mph, lem) {
  DSS.FormBase.call(this, mph, lem);
  this.type = 'form';
  this.form = frm;
  this.language = lang;
  this.linkedMSS = [];
  this.checkbox = undefined;
  for (var i = 0; i < lnk_mss.length; i++) {
    ms = lnk_mss[i];
    this.linkedMSS.push(ms);
  }
};
DSS.TextForm.constructor = DSS.TextForm;
DSS.TextForm.prototype = Object.create(DSS.FormBase.prototype);

DSS.TextForm.prototype.toString = function(){
  return this.form;
};
DSS.TextForm.prototype.hasLinkedMS = function(id){
  return this.linkedMSS.indexOf(id) > -1;
};
DSS.TextForm.prototype.linkedMSSCount = function(){
  return this.linkedMSS.length;
};
DSS.TextForm.prototype.getForm = function(){
  return this.form;
}
DSS.TextForm.prototype.getLinkedMSS = function(){
  return this.linkedMSS;
};

DSS.TextFormGroup = function () {
  DSS.FormBase.call('', '');
  this.type = 'textFormGroup';
  this.mainForm = undefined;
  this.sortedMSS = [];
  this.textForms = [];
};
DSS.TextFormGroup.constructor = DSS.TextFormGroup;
DSS.TextFormGroup.prototype = Object.create(DSS.FormBase.prototype);

DSS.TextFormGroup.prototype.toString = function(){
  return this.textForms.join(' ');
};
DSS.TextFormGroup.sortMSS = function (ms1, ms2) {
  if (ms1 == '19A') ms1 = 'VL19';
  if (ms2 == '19A') ms2 = 'VL19';

  ms1 = ms1.toLowerCase();
  ms2 = ms2.toLowerCase();
  var c1 = ms1.charAt(0);
  var c2 = ms2.charAt(0);
  var n1, n2;
  if (c1 == 'v' && c2 != 'v') {
    return 1;
  }
  else if (c2 == 'v' && c1 != 'v') {
    return -1;
  }
  else if (c1 == 'v' && c2 == 'v') {
    if (ms2 == 'vg') {
      return -1;
    }
    else if (ms1 == 'vg') {
      return 1;
    }
    else {
      n1 = Number(ms1.substring(2));
      n2 = Number(ms2.substring(2));
      if (n1 < n2) {
        return -1;
      }
      else {
        return 1;
      }
    }
  }

  if (c1 == 'p' && c2 != 'p') {
    return -1;
  }
  else if (c2 == 'p' && c1 != 'p') {
    return 1;
  }
  else if (c1 == 'p' && c2 == 'p') {
    n1 = Number(ms1.substr(1));
    n2 = Number(ms2.substr(1));
    if (n1 < n2) {
      return -1;
    }
    else if (n2 < n1) {
      return 1;
    }
  }
  if (c1 == '0' && c2 != '0') {
    return -1;
  }
  else if (c2 == '0' && c1 != '0') {
    return 1;
  }
  else if (c1 == '0' && c2 == '0') {
    n1 = Number(ms1.substr(1));
    n2 = Number(ms2.substr(1));
  }
  else {
    n1 = Number(ms1);
    n2 = Number(ms2);
  }
  if (n1 < n2) {
    return -1;
  }
  else if (n2 < n1) {
    return 1;
  }
  return 0;
};
DSS.TextFormGroup.prototype.sortMSS = function() {
  this.sortedMSS = [];
  var frm;
  for (var i = 0; i < this.textForms.length; i++) {
    frm = this.textForms[i];
    this.sortedMSS = this.sortedMSS.concat(frm.linkedMSS);
  }
  this.sortedMSS.sort(DSS.TextFormGroup.sortMSS);
};
DSS.TextFormGroup.prototype.addTextForm = function(frm, isInitMainForm){
  // Is passed form already a group?
  if (frm.type == 'textFormGroup') {
    for (var i = 0; i < frm.textForms.length; i++) {
      this.textForms.push(frm.textForms[i]);
    }
  }
  else {
    this.textForms.push(frm);
  }
  this.textForms.sort(function (f1, f2) {
    if (f1.language == 'greek' && f2.language == 'latin') {
      return -1;
    }
    else if (f1.language == 'latin' && f2.language == 'greek') {
      return 1;
    }
    else if (f1.linkedMSS.length > f2.linkedMSS.length) {
      return -1;
    }
    else if (f1.linkedMSS.length < f2.linkedMSS.length) {
      return 1;
    }
    else {
      return 0;
    }
  });
  this.sortMSS(); // for tooltip
  if (isInitMainForm) {
    this.mainForm = this.textForms[0].getForm();
    this.lemma = this.textForms[0].getLemma();
    this.morph = this.textForms[0].getMorph();
  }
};
DSS.TextFormGroup.prototype.hasLinkedMS = function(id){
  var hasLinked = false;
  var frm;
  for (var i = 0; i < this.textForms.length; i++) {
    frm = this.textForms[i];
    if (frm.hasLinkedMS(id)) {
      hasLinked = true;
      break;
    }
  }
  return hasLinked;
};
DSS.TextFormGroup.prototype.linkedMSSCount = function(){
  var count = 0;
  var frm;
  for (var i = 0; i < this.textForms.length; i++) {
    frm = this.textForms[i];
    count += frm.linkedMSS.length;
  }
  return count;
};
DSS.TextFormGroup.prototype.getForm = function(){
  return this.mainForm ? this.mainForm : '';
}
DSS.TextFormGroup.prototype.getLinkedMSS = function(){
  return this.sortedMSS;
};
DSS.TextFormGroup.handleCheck = function (subFrm, slot) {
  if (this.textForms.length > 2) { // remove checked item 
    var pos = this.textForms.indexOf(subFrm);
    if (pos > -1) {
      this.textForms.splice(pos, 1);
      slot.textForms.push(subFrm);
      if (subFrm.form == this.mainForm) {
        this.mainForm = this.textForms[0].getForm();
        this.morph = this.textForms[0].getMorph();
        this.lemma = this.textForms[0].getLemma();
      }
    }
    this.sortMSS();
  }
  else { // remove both items
    var pos = slot.textForms.indexOf(this);
    if (pos > -1) {
      slot.textForms.splice(pos, 1);
      for (var i = 0; i < this.textForms.length; i++) {
        var sf = this.textForms[i];
        slot.textForms.push(sf);
      }
    }
  }
  slot.refresh();
};
DSS.TextFormGroup.handleClick = function (subFrm, slot) {
  this.mainForm = subFrm.getForm();
  this.lemma = subFrm.getLemma();
  this.morph = subFrm.getMorph();
  slot.refresh();
};

DSS.ReadingUnit = function(t_idx, c_num, v_num, a_idx, txt) {
  DSS.AddressSlot.call(this, t_idx, c_num, v_num);
  this.type = 'readingUnit';
  this.addressIdx = a_idx;
  this.text = txt;
};
DSS.ReadingUnit.constructor = DSS.ReadingUnit;
DSS.ReadingUnit.prototype = Object.create(DSS.AddressSlot.prototype);

DSS.mssListToString = function(mss_list){
  mss_list.sort(DSS.TextFormGroup.sortMSS);

  var g_list = [];
  var l_list = [];
  var has_19A = false;
  var has_vg = false;
  for (var i = 0; i < mss_list.length; i++) {
    var ms = mss_list[i];
    if (ms.match(/^VL/)) {
      l_list.push(ms.substring(2));
    }
    else if (ms == '19A') {
      has_19A = true;
    }
    else if (ms == 'vg') {
      has_vg = true;
    }
    else {
      g_list.push(ms);
    }
  }

  if (has_19A) {
    l_list.push('19A');
  }

  var mss_str = '';
  if (g_list.length > 0) {
    mss_str = g_list.join(' ');
  }
  if (l_list.length > 0) {
    if (mss_str.length > 0) {
      mss_str = mss_str + ' ';
    }
    mss_str = mss_str + 'VL(' + l_list.join(' ') + ')';
  }
  if (has_vg) {
    if (mss_str.length > 0) {
      mss_str = mss_str + ' ';
    }
    mss_str = mss_str + 'vg';
  }
  return mss_str;
};

DSS.Reading = function () {
  this.type = 'reading';
  this.readingUnits = [];
  this.manuscripts = [];
  this.displayValue = '';
};
DSS.Reading.constructor = DSS.Reading;
DSS.Reading.prototype.toString = function(){
  var mss_str = ''
  if (this.manuscripts.length > 0) {
    mss_str = this.getText() + '] ' + DSS.mssListToString(this.manuscripts);
  }
  return mss_str;
};
DSS.Reading.prototype.hasManuscript = function(id){
  for (var i = 0; i < this.manuscripts.length; i++) {
    var ms = this.manuscripts[i];
    if (ms == id) {
      return true;
    }
  }
  return false;
};
DSS.Reading.prototype.manuscriptCount = function(){
  return this.manuscripts.length;
};
DSS.Reading.prototype.addManuscript = function(id){
  this.manuscripts.push(id);
  this.manuscripts.sort(DSS.TextFormGroup.sortMSS);
};
DSS.Reading.prototype.removeManuscript = function(id){
  for (var i = 0; i < this.manuscripts.length; i++) {
    var ms = this.manuscripts[i];
    if (ms == id) {
      this.manuscripts.splice(i, 1);
      break;
    }
  }
};
DSS.Reading.prototype.getText = function(){
  if (this.displayValue != '') {
    return this.displayValue;
  };

  var txt_str = '';
  var isOm = true;
  for (var i = 0; i < this.readingUnits.length; i++) {
    var ru = this.readingUnits[i];
    if (ru.text != 'om.') {
      isOm = false;
      break;
    }
  }
  if (isOm) { // all units = 'om.'
    txt_str = 'om.';
  }
  else {
    for (var i = 0; i < this.readingUnits.length; i++) {
      var ru = this.readingUnits[i];
      if (ru.text == 'om.') {
        continue;
      }
      if (txt_str.length > 0) {
        txt_str = txt_str + ' ';
      }
      txt_str = txt_str + ru.text;
    }
  }
  return txt_str;
};

DSS.ReadingGroup = function () {
  this.type = 'readingGroup';
  this.displayValue = '';
  this.manuscripts = [];
  this.readings = [];
};
DSS.ReadingGroup.constructor = DSS.Reading;
DSS.ReadingGroup.prototype.toString = function(){
  var mss_str = ''
  if (this.manuscripts.length > 0) {
    mss_str = this.getText() + '] ' + DSS.mssListToString(this.manuscripts);
  }
  return mss_str;
};
DSS.ReadingGroup.prototype.getText = function() {
  return this.displayValue;
};
DSS.ReadingGroup.prototype.sortMSS = function() {
  this.manuscripts = [];
  var rdg;
  for (var i = 0; i < this.readings.length; i++) {
    rdg = this.readings[i];
    this.manuscripts = this.manuscripts.concat(rdg.manuscripts);
  }
  this.manuscripts.sort(DSS.TextFormGroup.sortMSS);
};
DSS.ReadingGroup.prototype.hasManuscript = function(id){
  for (var i = 0; i < this.manuscripts.length; i++) {
    var ms = this.manuscripts[i];
    if (ms == id) {
      return true;
    }
  }
  return false;
};
DSS.ReadingGroup.prototype.manuscriptCount = function(){
  var count = 0;
  var rdg;
  for (var i = 0; i < this.readings.length; i++) {
    rdg = this.readings[i];
    count += rdg.manuscripts.length;
  }
  return count;
};
DSS.ReadingGroup.prototype.addReading = function(rdg){
  // Is passed form already a group?
  if (rdg.type == 'readingGroup') {
    for (var i = 0; i < rdg.readings.length; i++) {
      this.readings.push(rdg.readings[i]);
    }
  }
  else {
    this.readings.push(rdg);
  }
  this.readings.sort(function (f1, f2) {
    if (f1.manuscripts.length > f2.manuscripts.length) {
      return -1;
    }
    else if (f1.manuscripts.length < f2.manuscripts.length) {
      return 1;
    }
    else{
      return 0;
    }
  });
  this.sortMSS();
};

DSS.VariationUnit = function () {
  this.label = '';
  this.type = 'variationUnit';
  this.checkbox = undefined;
  this.addresses = [];
  this.readings = [];
  this.hasRetroversion = true;
};
DSS.VariationUnit.constructor = DSS.VariationUnit;
DSS.VariationUnit.prototype.toString = function(){
  var str = '';
  for (var i = 0; i < this.readings.length; i++) {
    var reading = this.readings[i];
    if (str.length > 0) {
      str = str + ' ';
    }
    str = str + reading.toString();
  }
  return str;
};
DSS.VariationUnit.prototype.isSingular = function() {
  var nonSing = 0;
  for (var i = 0; i < this.readings.length; i++) {
    var reading = this.readings[i];
    if (reading.manuscriptCount() > 1) {
      nonSing++;
    }
  }
  return nonSing == 1;
};
DSS.VariationUnit.prototype.isBezaeSingular = function() {
  var reading = this.getReadingForManuscript('05');
  if (reading && reading.manuscriptCount() == 1) {
    return true;
  }
  else if (reading && reading.hasManuscript('VL5') && reading.manuscriptCount() == 2) {
    return true;
  }
  return false;
};
DSS.VariationUnit.prototype.isBezaeColumnDiff = function() {
  var D = this.getReadingForManuscript('05');
  var d = this.getReadingForManuscript('VL5');
  if (!d || ! D) {
    return false;
  }
  if (d.getText() != D.getText()) {
    return true;
  }
  return false;
};
DSS.VariationUnit.prototype.getReadingForManuscript = function(ms) {
  for (var i = 0; i < this.readings.length; i++) {
    var reading = this.readings[i];
    if (reading.hasManuscript(ms)) {
      return reading;
    }
  }
  return undefined;
};
DSS.VariationUnit.prototype.getReadingByText = function(text) {
  for (var i = 0; i < this.readings.length; i++) {
    var reading = this.readings[i];
    if (reading.getText() == text) {
      return reading;
    }
  }
  return undefined;
};
DSS.VariationUnit.prototype.getAddress = function() {
  var verse = this.addresses[0].verseNum;
  var addrIdx = this.addresses[0].addressIdx;
  return DSS.chapter.getAddress(verse, addrIdx);
};
DSS.VariationUnit.prototype.getReference = function() {
  var label = '';
  var lastAddr = undefined;
  var tokens = [];
  for (var i = 0; i < this.addresses.length; i++) {
    var addr = this.addresses[i];
    if (tokens.length == 0) {
      tokens.push(addr.tokenIdx);
    }
    else {
      var diff = 1;
      if (addr.addressIdx == '1') {
        diff = 2;
      }
      if (parseInt(addr.tokenIdx) - parseInt(lastAddr.tokenIdx) == diff) {
        if (tokens[tokens.length - 1] != '-') {
          tokens.push('-');
        }
      }
      else {
        if (tokens[tokens.length - 1] == '-') {
          tokens.push(lastAddr.tokenIdx);
        }
        tokens.push(',');
        tokens.push(addr.tokenIdx);
      }
    }
    lastAddr = addr;
  }
  if (tokens[tokens.length - 1] == ',' || tokens[tokens.length - 1] == '-') {
    tokens.push(lastAddr.tokenIdx);
  }
  lastAddr = undefined;
  for (var i = 0; i < tokens.length; i++) {
    var tok = tokens[i];
    var addr = DSS.chapter.addresses[tok];
    if (i == 0) {
      label = addr.verseNum + '.' + addr.addressIdx;
      lastAddr = addr;
    }
    else if (tok == ',' || tok == '-') {
      label = label + tok;
    }
    else {
      if (addr.verseNum == lastAddr.verseNum) {
        label = label + addr.addressIdx
      }
      else {
        label = label + addr.verseNum + '.' + addr.addressIdx;
      }
      lastAddr = addr;
    }
  }
  return lastAddr.chapterNum + '.' + label;
};
DSS.VariationUnit.prototype.getUnlinkedMSS = function() {
  var unlinked = [];
  for (var i = 0; i < DSS.chapter.manuscripts.length; i++) {
    var ms = DSS.chapter.manuscripts[i];
    if (!this.getReadingForManuscript(ms)) {
      unlinked.push(ms);
    }
  };
  return unlinked;
};
DSS.VariationUnit.prototype.initialize = function(addrs) {
  var readingsMap = {};
  for (var i = 0; i < DSS.chapter.manuscripts.length; i++) {
    var ms = DSS.chapter.manuscripts[i];
    var readingUnits = [];
    for (var j = 0; j < addrs.length; j++) {
      var addr = addrs[j];
      var frm = addr.manuscriptForms[ms];
      if (!frm) {
        continue;
      }

      var readingUnit = new DSS.ReadingUnit(addr.tokenIdx, DSS.chapter.chapterNum, addr.verseNum, addr.addressIdx, frm.getForm());
      readingUnits.push(readingUnit);
    }
    var tempReading = new DSS.Reading();
    tempReading.readingUnits = readingUnits;
    var text = tempReading.getText();
    if (!text || readingUnits.length == 0) {
      continue;
    }
    var reading;
    if (text in readingsMap) {
      reading = readingsMap[text];
    }
    else {
      reading = new DSS.Reading();
      reading.readingUnits = readingUnits;
      readingsMap[text] = reading;
      this.readings.push(reading);
    }
    reading.manuscripts.push(ms);
  }
  this.readings.sort(DSS.VariationUnit.sortReadings);
  this.addresses = addrs;
  this.label = this.getReference();
};
DSS.VariationUnit.sortReadings = function (r1, r2) {
  if (r1.manuscriptCount() > r2.manuscriptCount()) {
    return -1;
  }
  else if (r1.manuscriptCount() < r2.manuscriptCount()) {
    return 1;
  }
  else {
    return 0;
  }
};
DSS.VariationUnit.prototype.applyManuscript = function(rspan, ms) {
  if (ms == '35') {
    rspan.removeClass('ms-bezae');
    rspan.removeClass('ms-vaticanus');
    rspan.addClass('ms-mainstream');
  }
  else if (ms == '05') {
    rspan.removeClass('ms-vaticanus');
    rspan.addClass('ms-bezae');
  }
  else if (ms == '03') {
    rspan.addClass('ms-vaticanus');
  }
};
DSS.VariationUnit.prototype.render = function(cell) {
  var stopProp = function(event){ event.stopPropagation(); }

  cell.empty();
  cell.removeAttr('class');
  cell.removeAttr('title');
  cell.unbind();

  var wrapper = $('<span>');
  cell.attr('title', this.toString());
  var cb = $('<input>', {type:'checkbox'});
  cb.click(stopProp);
  this.checkbox = cb;
  cell.append(cb);
  wrapper.append(this.label);
  cell.append(wrapper);
  cell.addClass('popup');
  cell.addClass('simpleButton');
  if (this.isSingular()) {
    wrapper.addClass('singular');
  }
  if (!this.hasRetroversion) {
    wrapper.addClass('noRetroversion');
  }
  if (this.isBezaeSingular()) {
    wrapper.addClass('bezaeSingular');
  }
  if (this.isBezaeColumnDiff()) {
    wrapper.addClass('columnDiff');
  }

  this.popup = $('<div>', {class: 'popuptext'});
  this.popup.click(stopProp);

  var row = 0;
  var HROW = 25;

  // Variation unit label
  var lspan = $('<span>', {text: this.label, class: 'ms'});
  this.popup.append(lspan);

  wrapper = $('<span>', {class: 'ms'});
  wrapper.css('top', row * HROW);
  wrapper.css('left', 400);
  this.retrobox = $('<input>', {type: 'checkbox'});
  if (this.hasRetroversion) {
    this.retrobox.prop('checked', true);
  }
  else {
    this.retrobox.prop('checked', false);
  }
  this.retrobox.click(stopProp);
  wrapper.append('Has retroversion?', this.retrobox);
  this.popup.append(wrapper);

  // Reading selection
  row++;
  wrapper = $('<span>', {class: 'ms'});
  wrapper.css('top', row * HROW);
  this.select = $('<select>');
  var option = $('<option>', {text: 'None'});
  this.select.append(option);
  for (var i = 0; i < this.readings.length; i++) {
    var reading = this.readings[i];
    option = $('<option>', {text: reading.getText(), value: reading.getText()});
    this.select.append(option);
  }
  wrapper.append(this.select);
  this.popup.append(wrapper);

  // Reading / cb pairs
  this.r_cboxes = [];

  // MS / cb pairs
  this.ms_cboxes = [];

  // Reading group main form text boxes
  this.r_tboxes = [];
  for (var i = 0; i < this.readings.length; i++) {
    var reading = this.readings[i];
    cb = $('<input>', {type: 'checkbox'});
    cb.click(stopProp);
    var rtext = reading.getText();
    var rspan = $('<span>', {class: 'reading', title: rtext});
    row++;
    rspan.css('top', row * HROW);
    rspan.append([cb, rtext]);
    this.popup.append(rspan);
    this.r_cboxes.push({ 'checkbox': cb, 'reading': reading});

    wrapper = $('<span>', {class: 'ms'});
    wrapper.css('top', row * HROW);
    wrapper.css('left', 400);
    var tbox = $('<input>', {type: 'text', value: rtext});
    tbox.css('width', 375);
    this.r_tboxes.push({'textbox': tbox, 'reading': reading});
    wrapper.append(tbox);
    this.popup.append(wrapper);

    // Select subreadings
    if (reading.type == 'readingGroup') {
      for (var j = 0; j < reading.readings.length; j++) {
        var subrdg = reading.readings[j];
        row++;
        wrapper = $('<span>', {class: 'ms'});
        wrapper.addClass('subreading');
        wrapper.css('top', row * HROW);
        wrapper.css('left', 10);
        rtext = subrdg.getText();
        wrapper.append(rtext);
        this.popup.append(wrapper);
        for (var k = 0; k < subrdg.manuscripts.length; k++) {
          var ms = subrdg.manuscripts[k];
          if (k % 16 == 0) {
            row++;
          }
          cb = $('<input>', {type:'checkbox'});
          cb.click(stopProp);
          var span = $('<span>', {class: 'ms'});
          span.css('left', (k % 16) * 50);
          span.css('top', row * HROW);
          this.applyManuscript(rspan, ms);
          span.append([cb, ms]);
          this.popup.append(span);
          this.ms_cboxes.push({ 'checkbox': cb, 'manuscript': ms});
        }
      }
    }
    else {
      for (var j = 0; j < reading.manuscripts.length; j++) {
        var ms = reading.manuscripts[j];
        if (j % 16 == 0) {
          row++;
        }
        cb = $('<input>', {type:'checkbox'});
        cb.click(stopProp);
        var span = $('<span>', {class: 'ms'});
        span.css('left', (j % 16) * 50);
        span.css('top', row * HROW);
        this.applyManuscript(rspan, ms);
        span.append([cb, ms]);
        this.popup.append(span);
        this.ms_cboxes.push({ 'checkbox': cb, 'manuscript': ms});
      }
    }
  }

  // Unassigned MSS
  var rspan = $('<span>', {text: 'None', class: 'reading'});
  row++;
  rspan.css('top', row * HROW);
  this.popup.append(rspan);
  var unlinked = this.getUnlinkedMSS();
  for (var j = 0; j < unlinked.length; j++) {
    var ms = unlinked[j];
    if (j % 16 == 0) {
      row++;
    }
    cb = $('<input>', {type:'checkbox'});
    cb.click(stopProp);
    var span = $('<span>', {class: 'ms'});
    span.css('left', (j % 16) * 50);
    span.css('top', row * HROW);
    this.applyManuscript(rspan, ms);
    span.append([cb, ms]);
    this.popup.append(span);
    this.ms_cboxes.push({ 'checkbox': cb, 'manuscript': ms});
  }
  
  // Buttons
  row++;
  var btn1 = $('<span>', {text: 'Save', class: 'button'});
  btn1.css('top', row * HROW);
  btn1.css('left', 300);
  btn1.bind('click', DSS.VariationUnit.handleSave.bind(this));

  var btn2 = $('<span>', {text: 'Cancel', class: 'button'});
  btn2.css('top', row * HROW);
  btn2.css('left', 420);
  btn2.bind('click', DSS.VariationUnit.handleClose.bind(this));

  this.popup.append([btn1, btn2]);

  row++;
  this.popup.css('height', row * HROW);
  cell.append(this.popup);
  cell.bind('click', DSS.VariationUnit.handleClick.bind(this));
};
DSS.VariationUnit.handleCheck = function (slot) {
  for (var i = 0; i < slot.variationUnits.length; i++) {
    var varunit = slot.variationUnits[i];
    if (varunit.label == this.label) {
      slot.variationUnits.splice(i, 1);
      break;
    }
  }
  slot.refresh();
};
DSS.VariationUnit.handleClick = function () {
  if (!this.popup.hasClass('show')) {
    $('.popup .popuptext.show').each(function(i, obj) {
      $(this).removeClass('show');
    });
    this.popup.addClass('show');
  }
  else {
    this.popup.removeClass('show');
  }
};
DSS.VariationUnit.handleSave = function (event) {
  var selectedMSS = 0;
  for (var i = 0; i < this.ms_cboxes.length; i++) {
    var map = this.ms_cboxes[i];
    var cb = map['checkbox'];
    if (cb.is(':checked')) {
      selectedMSS++;
    }
  }

  var selectedReadings = 0;
  for (var i = 0; i < this.r_cboxes.length; i++) {
    var map = this.r_cboxes[i];
    var cb = map['checkbox'];
    var rdg = map['reading'];
    if (cb.is(':checked')) {
      if (rdg.type == 'readingGroup') {
        selectedReadings = selectedReadings + 2;
      }
      else {
        selectedReadings++;
      }
    }
  }

  if (this.retrobox.is(':checked')) {
    this.hasRetroversion = true;
  }
  else {
    this.hasRetroversion = false;
  }
  for (var i = 0; i < this.r_tboxes.length; i++) {
    var map = this.r_tboxes[i];
    var tb = map['textbox'];
    var rdg = map['reading'];
    rdg.displayValue = tb.val();
  }
  if (selectedReadings > 1) {
    // Proceed if two or more readings checked or one group is checked
    var group = new DSS.ReadingGroup();
    for (var i = this.r_cboxes.length - 1; i >= 0; i--) {
      var map = this.r_cboxes[i];
      var cb = map['checkbox'];
      var rdg = map['reading'];
      if (cb.is(':checked')) {
        if (rdg.type == 'readingGroup') { // Remove checked group
          this.readings.splice(i, 1);
          for (var j = 0; j < rdg.readings.length; j++) {
            this.readings.push(rdg.readings[j]);
          }
        }
        else { // Add checked form
          group.addReading(rdg);
          this.readings.splice(i, 1);
        }
      }
    }
    if (group.readings.length > 0) {
      group.displayValue = group.readings[0].getText();
      this.readings.push(group);
    }
    this.readings.sort(DSS.VariationUnit.sortReadings);
  }
  else {
    var reading = this.select.val();
    for (var i = 0; i < this.ms_cboxes.length; i++) {
      var map = this.ms_cboxes[i];
      var cb = map['checkbox'];
      var ms = map['manuscript'];
      if (cb.is(':checked')) {
        // remove from currently-assigned reading
        var oldReading = this.getReadingForManuscript(ms);
        if (oldReading) { // not 'None'
          oldReading.removeManuscript(ms);
        }

        // assign to new reading
        if (reading != 'None') {
          var newReading = this.getReadingByText(reading);
          newReading.addManuscript(ms);
        }

        cb.prop('checked', false);
      }
    }
  }
  this.getAddress().refresh();
  event.stopPropagation();
};
DSS.VariationUnit.handleClose = function (event) {
  this.popup.removeClass('show');
  event.stopPropagation();
};