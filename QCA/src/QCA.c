# include <R.h>
# include <Rinternals.h>
# include <Rmath.h>
# include <R_ext/Rdynload.h>
void increment(int, int*, int*, int, int[]);
void fillMatrix(int, int, int[], int*, int, int[], int); 
void calculateRows(int, int[], int, int, int*);
void generateMatrix(int, int, int[], int, int, SEXP);
void increment(int k, int *e, int *h, int nconds, int tempk[]) {
    if (*e < nconds - *h) {
        *h = 1;
        *e = tempk[k - 1] + 1;
        tempk[k - 1] += 1;
    }
    else {
        *e = tempk[k - *h - 1] + 1;
        *h += 1; 
        for (int j = 0; j < *h; j++) {
            tempk[k - *h + j] = *e + j;
        }
    }
}
void fillMatrix(int nrows, int ncols, int nofl[], int *matrix, int startrow, int cols[], int plus1) {
    int mbase[ncols];
    int orep[ncols];
    for (int c = 0; c < ncols; c++) {
        if (c == 0) {
            mbase[ncols - c - 1] = 1;
            orep[c] = 1;
        }
        else {
            mbase[ncols - c - 1] = mbase[ncols - c] * nofl[ncols - c];
            orep[c] = orep[c - 1] * nofl[c - 1];
        }
    }
    for (int c = 0; c < ncols; c++) {
        int lt = mbase[c] * nofl[c];
        for (int o = 0; o < orep[c]; o++) {
            for (int l = 0; l < nofl[c]; l++) {
                for (int i = 0; i < mbase[c]; i++) {
                    matrix[startrow + nrows * cols[c] + lt * o + mbase[c] * l + i] = l + plus1;
                }
            }
        }
    }
}
void calculateRows(int ncols, int nofl[], int arrange, int maxprod, int *rows) {
    *rows = 0;
    int e, h, k, prod;
    if (arrange == 0) {
        *rows = 1;
        int cols[ncols];
        for (int c = 0; c < ncols; c++) {
            *rows *= nofl[c]; 
            cols[c] = c;
        }
    }
    else {
        for (k = 1; k <= maxprod; k++) {
            int tempk[k];
            int nck;
            nck = 1;
            for (int i = 1; i <= k; i++) {
                nck *= ncols - (k - i);
                nck /=  i;
            }
            for (int i = 0; i < k; i++) {
                tempk[i] = i;
            }
            e = 0;
            h = k;
            for (int count = 0; count < nck; count++) {
                if (count > 0) {
                    increment(k, &e, &h, ncols, tempk);
                }
                prod = 1;
                for (int c = 0; c < k; c++) {
                    prod *= (nofl[tempk[c]] - 1);
                }
                *rows += prod;
            }
        }
    }
}
void generateMatrix(int nrows, int ncols, int nofl[], int arrange, int maxprod, SEXP matrix) {
    int *p_matrix = INTEGER(matrix);
    int e, h, k, prod;
    if (arrange == 0) {
        int cols[ncols];
        for (int c = 0; c < ncols; c++) {
            cols[c] = c;
        }
        fillMatrix(nrows, ncols, nofl, p_matrix, 0, cols, 0);
    }
    else { 
        for (int i = 0; i < nrows * ncols; i++) {
            p_matrix[i] = 0;
        }
        int startrow = 0;
        for (k = 1; k <= maxprod; k++) {
            int tempk[k];
            int nck;
            nck = 1;
            for (int i = 1; i <= k; i++) {
                nck *= ncols - (k - i);
                nck /=  i;
            }
            for (int i = 0; i < k; i++) {
                tempk[i] = i;
            }
            e = 0;
            h = k;
            for (int count = 0; count < nck; count++) {
                if (count > 0) {
                    increment(k, &e, &h, ncols, tempk);
                }
                prod = 1;
                int colsk[k];
                int noflk[k];
                for (int c = 0; c < k; c++) {
                    prod *= (nofl[tempk[c]] - 1);
                    colsk[c] = tempk[c];
                    noflk[c] = nofl[tempk[c]] - 1;
                }
                fillMatrix(nrows, k, noflk, p_matrix, startrow, colsk, 1);
                startrow += prod;
            }
        }
    }
}
SEXP createMatrix(SEXP noflevels, SEXP arrange, SEXP maxprod) {
    SEXP matrix;
    SEXP usage = PROTECT(allocVector(VECSXP, 4));
    SET_VECTOR_ELT(usage, 0, noflevels = coerceVector(noflevels, INTSXP));
    SET_VECTOR_ELT(usage, 1, arrange = coerceVector(arrange, INTSXP));
    SET_VECTOR_ELT(usage, 2, maxprod = coerceVector(maxprod, INTSXP));
    int *p_noflevels = INTEGER(noflevels);
    int *p_arrange = INTEGER(arrange);
    int *p_maxprod = INTEGER(maxprod);
    int ncols = length(noflevels);
    int nofl[ncols];
    for (int c = 0; c < ncols; c++) {
        nofl[c] = p_noflevels[c];
    }
    if (p_maxprod[0] > ncols) {
        p_maxprod[0] = ncols;
    }
    int intarrange = p_arrange[0];
    int intmaxprod = p_maxprod[0];
    int nrows;
    calculateRows(ncols, nofl, intarrange, intmaxprod, &nrows);
    SET_VECTOR_ELT(usage, 3, matrix = allocMatrix(INTSXP, nrows, ncols));
    generateMatrix(nrows, ncols, nofl, intarrange, intmaxprod, matrix);
    UNPROTECT(1);
    return(matrix);
}
SEXP superSubset(SEXP x, SEXP noflevels, SEXP fuz, SEXP vo,
                 SEXP nec, SEXP inclcut, SEXP covcut, SEXP depth) {
    SEXP usage = PROTECT(allocVector(VECSXP, 19));
    SET_VECTOR_ELT(usage,  0, x         = coerceVector(x, REALSXP));
    SET_VECTOR_ELT(usage,  1, noflevels = coerceVector(noflevels, INTSXP));
    SET_VECTOR_ELT(usage,  2, fuz       = coerceVector(fuz, INTSXP));
    SET_VECTOR_ELT(usage,  3, vo        = coerceVector(vo, REALSXP));
    SET_VECTOR_ELT(usage,  4, nec       = coerceVector(nec, INTSXP));
    SET_VECTOR_ELT(usage,  5, inclcut   = coerceVector(inclcut, REALSXP));
    SET_VECTOR_ELT(usage,  6, covcut    = coerceVector(covcut, REALSXP));
    SET_VECTOR_ELT(usage,  7, depth     = coerceVector(depth, INTSXP));
    double *p_x = REAL(x);
    int *p_noflevels = INTEGER(noflevels);
    int *p_fuz = INTEGER(fuz);
    double *p_vo = REAL(vo);
    int *p_nec = INTEGER(nec);
    double *p_inclcut = REAL(inclcut);
    double *p_covcut = REAL(covcut);
    int *p_depth = INTEGER(depth);
    int estim1 = 1000;
    int estim2 = 1000; 
    int xrows = nrows(x);
    int xcols = ncols(x);
    int nconds = ncols(x); 
    if (p_depth[0] == 0) {
        p_depth[0] = nconds;
    }
    SEXP tmconj, tmdisj, ticpr_conj, ticpr_disj, combkl, tcoms_conj, tcoms_disj,
         indx_conj, indx_disj, ck_conj, ck_disj;
    SET_VECTOR_ELT(usage,  8, tmconj     = allocVector(INTSXP, nconds * estim1));
    SET_VECTOR_ELT(usage,  9, tmdisj     = allocVector(INTSXP, nconds * estim2));
    SET_VECTOR_ELT(usage, 10, ticpr_conj = allocVector(REALSXP, 3 * estim1));    
    SET_VECTOR_ELT(usage, 11, ticpr_disj = allocVector(REALSXP, 3 * estim2));    
    SET_VECTOR_ELT(usage, 12, tcoms_conj = allocMatrix(REALSXP, xrows, estim1)); 
    SET_VECTOR_ELT(usage, 13, tcoms_disj = allocMatrix(REALSXP, xrows, estim1)); 
    SET_VECTOR_ELT(usage, 14, indx_conj  = allocVector(INTSXP, p_depth[0] * estim1)); 
    SET_VECTOR_ELT(usage, 15, indx_disj  = allocVector(INTSXP, p_depth[0] * estim2)); 
    SET_VECTOR_ELT(usage, 16, ck_conj    = allocVector(INTSXP, estim1)); 
    SET_VECTOR_ELT(usage, 17, ck_disj    = allocVector(INTSXP, estim2)); 
    int    *p_tmconj     = INTEGER(tmconj);
    int    *p_tmdisj     = INTEGER(tmdisj);
    double *p_ticpr_conj = REAL(ticpr_conj);
    double *p_ticpr_disj = REAL(ticpr_disj);
    double *p_tcoms_conj = REAL(tcoms_conj);
    double *p_tcoms_disj = REAL(tcoms_disj);
    int    *p_indx_conj  = INTEGER(indx_conj);
    int    *p_indx_disj  = INTEGER(indx_disj);
    int    *p_ck_conj    = INTEGER(ck_conj);
    int    *p_ck_disj    = INTEGER(ck_disj);
    double copyline[nconds], minx[xrows], maxx[xrows];
    double incovpron[6];
    double so = 0.0,
           min, max,
           sum_minx,
           sum_maxx,
           sum_1_minx,
           sum_1_maxx,
           sum_1_min_y_minx,
           sum_1_min_y_maxx,
           sum_min_y_minx,
           sum_min_y_maxx,
           prisum_minx,
           prisum_maxx,
           tmpv11, tmpv12, tmpv21, tmpv22;
    int found1 = 0;
    int found = 0;
    int foundk1 = 0;
    int foundk2 = 0;
    if (nconds < p_depth[0]) {
        p_depth[0] = nconds;
    }
    for (int i = 0; i < length(vo); i++) {
        so += p_vo[i];
    }
    int chkred[nconds], inclcov;
    int k = 1;
    int foundk = 1;
    while (k <= p_depth[0] && foundk) {
        if (found1 + found > 0 && k > 3) {
            foundk = 0;
        }
        int klnofl[k];
        int tempk[k];
        for (int i = 0; i < k; i++) {
            tempk[i] = i;
        }
        int e = 0;
        int h = k;
        int kmatcol = 0;
        while (tempk[0] != nconds - k || !kmatcol) {
            if (kmatcol) {
                increment(k, &e, &h, nconds, tempk);
            }
            kmatcol = 1;
            int klcols[k];
            int klrows = 1;
            for (int j = 0; j < k; j++) {
                klnofl[j] = p_noflevels[tempk[j]];
                klrows *= klnofl[j];
                klcols[j] = j;
            }
            SET_VECTOR_ELT(usage, 18, combkl = allocVector(INTSXP, klrows * k));
            int *p_combkl = INTEGER(combkl);
            fillMatrix(klrows, k, klnofl, p_combkl, 0, klcols, 0);
            for (int kli = 0; kli < klrows; kli++) {
                for (int c = 0; c < nconds; c++) {
                    chkred[c] = 0;
                }
                for (int j = 0; j < k; j++) {
                    chkred[tempk[j]] = p_combkl[j * klrows + kli] + 1; 
                }
                sum_minx = 0;         
                sum_maxx = 0;         
                sum_min_y_minx = 0;   
                sum_min_y_maxx = 0;   
                prisum_minx = 0;      
                prisum_maxx = 0;      
                sum_1_minx = 0;       
                sum_1_min_y_minx = 0; 
                sum_1_maxx = 0;       
                sum_1_min_y_maxx = 0; 
                for (int r = 0; r < xrows; r++) { 
                    min = 1000000;        
                    max = 0;
                    for (int c = 0; c < xcols; c++) { 
                        copyline[c] = p_x[c * xrows + r];
                        if (p_fuz[c]) { 
                            if (chkred[c] == 1) {
                                copyline[c] = 1 - copyline[c];
                            }
                        }
                        else {
                            if (chkred[c] == (copyline[c] + 1)) {
                                copyline[c] = 1; 
                            }
                            else {
                                copyline[c] = 0; 
                            }
                        }
                        if (chkred[c] != 0) {
                            if (copyline[c] < min) {
                                min = copyline[c]; 
                            }
                            if (copyline[c] > max) {
                                max = copyline[c]; 
                            }
                        }
                    } 
                    minx[r] = min;   
                    maxx[r] = max;   
                    sum_minx += min; 
                    sum_maxx += max; 
                    sum_min_y_minx += (min < p_vo[r])?min:p_vo[r];
                    sum_min_y_maxx += (max < p_vo[r])?max:p_vo[r];
                    if (p_nec[0]) {  
                        sum_1_minx += 1 - min;                                  
                        sum_1_maxx += 1 - max;                                  
                        sum_1_min_y_minx += 1 - ((min < p_vo[r])?min:p_vo[r]);  
                        sum_1_min_y_maxx += 1 - ((max < p_vo[r])?max:p_vo[r]);  
                    }
                    else {           
                        tmpv11 = (min < p_vo[r])?min:p_vo[r];
                        tmpv12 = p_nec[0]?(1 - min):(1 - p_vo[r]);
                        prisum_minx += (tmpv11 < tmpv12)?tmpv11:tmpv12;
                        tmpv21 = (max < p_vo[r])?max:p_vo[r];
                        tmpv22 = 1 - max;
                        prisum_maxx += (tmpv21 < tmpv22)?tmpv21:tmpv22;
                    }
                } 
                incovpron[0] = (sum_min_y_minx == 0 && sum_minx == 0)?0:(sum_min_y_minx/sum_minx);
                incovpron[1] = (sum_min_y_minx == 0 && so == 0)?0:(sum_min_y_minx/so);
                incovpron[2] = (sum_min_y_maxx == 0 && so == 0)?0:(sum_min_y_maxx/so);
                incovpron[3] = (sum_min_y_maxx == 0 && sum_maxx == 0)?0:(sum_min_y_maxx/sum_maxx);
                if (p_nec[0]) {
                    incovpron[4] = (sum_1_minx == 0 && sum_1_min_y_minx == 0)?0:(sum_1_minx/sum_1_min_y_minx);
                    incovpron[5] = (sum_1_maxx == 0 && sum_1_min_y_maxx == 0)?0:(sum_1_maxx/sum_1_min_y_maxx);
                }
                else {
                    tmpv11 = sum_min_y_minx - prisum_minx;
                    tmpv12 = (p_nec[0]?so:sum_minx) - prisum_minx;
                    incovpron[4] = (tmpv11 == 0 && tmpv12 == 0)?0:(tmpv11/tmpv12);
                    tmpv21 = sum_min_y_maxx - prisum_maxx;
                    tmpv22 = so - prisum_maxx;
                    incovpron[5] = (tmpv21 == 0 && tmpv22 == 0)?0:(tmpv21/tmpv22);
                }
                inclcov = incovpron[p_nec[0]] >= p_inclcut[0] && incovpron[1 - p_nec[0]] >= p_covcut[0];
                int redundant = 0;
                if (inclcov) {
                    if (foundk1 > 0 && !p_nec[0]) { 
                        int i = 0;
                        while (i < foundk1 && !redundant) {
                            int sumeq = 0;
                            int v = 0;
                            while (sumeq == v && v < p_ck_conj[i]) {
                                for (int c = 0; c < k; c++) {
                                    if (p_indx_conj[i * p_depth[0] + v] == tempk[c] + 1) {
                                        sumeq += (p_tmconj[i * nconds + p_indx_conj[i * p_depth[0] + v] - 1] == chkred[tempk[c]]);
                                    }
                                }
                                v += 1;
                            }
                            if (sumeq == v) {
                                redundant = 1;
                            }
                            i += 1;
                        }
                    }
                    if (!redundant) { 
                        for (int c = 0; c < nconds; c++) {
                            p_tmconj[found1 * nconds + c] = chkred[c];
                        }
                        p_ticpr_conj[found1 * 3 + 0] = incovpron[p_nec[0]];
                        p_ticpr_conj[found1 * 3 + 1] = incovpron[4];
                        p_ticpr_conj[found1 * 3 + 2] = incovpron[1 - p_nec[0]];
                        for (int r = 0; r < xrows; r++) {
                            p_tcoms_conj[found1 * xrows + r] = minx[r];
                        }
                        for (int c = 0; c < k; c++) {
                            p_indx_conj[p_depth[0] * found1 + c] = tempk[c] + 1;
                        }
                        p_ck_conj[found1] = k;
                        foundk += 1;
                        found1 += 1;
                        if (found1 == estim1) {
                            int copytm_conj[nconds * found1];
                            int tindx_conj[p_depth[0] * found1];
                            int tck_conj[found1];
                            double copyticpr_conj[3 * found1];
                            double copytcoms_conj[xrows * found1];
                            for (int i = 0; i < nconds * found1; i++) {
                                copytm_conj[i] = p_tmconj[i];
                            }
                            for (int i = 0; i < 3 * found1; i++) {
                                copyticpr_conj[i] = p_ticpr_conj[i];
                            }
                            for (int i = 0; i < xrows * found1; i++) {
                                copytcoms_conj[i] = p_tcoms_conj[i];
                            }
                            for (int i = 0; i < p_depth[0] * found1; i++) {
                                tindx_conj[i] = p_indx_conj[i];
                            }
                            for (int i = 0; i < found1; i++) {
                                tck_conj[i] = p_ck_conj[i];
                            }
                            estim1 *= 2;
                            SET_VECTOR_ELT(usage, 8,  tmconj     = allocVector(INTSXP, nconds * estim1));
                            p_tmconj = INTEGER(tmconj);
                            SET_VECTOR_ELT(usage, 10, ticpr_conj = allocVector(REALSXP, 3 * estim1));
                            p_ticpr_conj = REAL(ticpr_conj);
                            SET_VECTOR_ELT(usage, 12, tcoms_conj = allocMatrix(REALSXP, xrows, estim1));
                            p_tcoms_conj = REAL(tcoms_conj);
                            SET_VECTOR_ELT(usage, 14, indx_conj  = allocVector(INTSXP, p_depth[0] * estim1));
                            p_indx_conj = INTEGER(indx_conj);
                            SET_VECTOR_ELT(usage, 16, ck_conj    = allocVector(INTSXP, estim1));
                            p_ck_conj = INTEGER(ck_conj);
                            for (int i = 0; i < nconds * found1; i++) {
                                p_tmconj[i] = copytm_conj[i];
                            }
                            for (int i = 0; i < 3 * found1; i++) {
                                p_ticpr_conj[i] = copyticpr_conj[i];
                            }
                            for (int i = 0; i < xrows * found1; i++) {
                                p_tcoms_conj[i] = copytcoms_conj[i];
                            }
                            for (int i = 0; i < p_depth[0] * found1; i++) {
                                p_indx_conj[i] = tindx_conj[i];
                            }
                            for (int i = 0; i < found1; i++) {
                                p_ck_conj[i] = tck_conj[i];
                            }
                        }
                    }
                }
                else {
                    if (p_nec[0]) {
                        inclcov = incovpron[2] >= p_inclcut[0] && incovpron[3] >= p_covcut[0];
                        redundant = 0;
                        if (inclcov && foundk1 > 0) {
                            int i = 0;
                            while (i < foundk1 && !redundant) {
                                int sumeq = 0;
                                int v = 0;
                                while (sumeq == v && v < p_ck_conj[i]) {
                                    for (int c = 0; c < k; c++) {
                                        if (p_indx_conj[i * p_depth[0] + v] == tempk[c] + 1) {
                                            sumeq += (p_tmconj[i * nconds + p_indx_conj[i * p_depth[0] + v] - 1] == chkred[tempk[c]]);
                                        }
                                    }
                                    v += 1;
                                }
                                if (sumeq == v) {
                                    redundant = 1;
                                }
                                i += 1;
                            }
                        }
                        if (inclcov && foundk2 > 0 && !redundant) {
                            int i = 0;
                            while (i < foundk2 && !redundant) {
                                int sumeq = 0;
                                int v = 0;
                                while (sumeq == v && v < p_ck_disj[i]) {
                                    for (int c = 0; c < k; c++) {
                                        if (p_indx_disj[i * p_depth[0] + v] == tempk[c] + 1) {
                                            sumeq += (p_tmdisj[i * nconds + p_indx_disj[i * p_depth[0] + v] - 1] == chkred[tempk[c]]);
                                        }
                                    }
                                    v += 1;
                                }
                                if (sumeq == v) {
                                    redundant = 1;
                                }
                                i += 1;
                            }
                        }
                        if (inclcov && !redundant) {
                            for (int c = 0; c < nconds; c++) {
                                p_tmdisj[found * nconds + c] = chkred[c];
                            }
                            p_ticpr_disj[found * 3 + 0] = incovpron[2];
                            p_ticpr_disj[found * 3 + 1] = incovpron[5];
                            p_ticpr_disj[found * 3 + 2] = incovpron[3];
                            for (int r = 0; r < xrows; r++) {
                                p_tcoms_disj[found * xrows + r] = maxx[r];
                            }
                            p_ck_disj[found] = k;
                            for (int c = 0; c < k; c++) {
                                p_indx_disj[p_depth[0] * found + c] = tempk[c] + 1;
                            }
                            foundk += 1;
                            found += 1;
                            if (found == estim2) {
                                int copytmdisj[nconds * found];
                                int tindx_disj[p_depth[0] * found];
                                int tck_disj[found];
                                double copyticpr_disj[3 * found];
                                double copytcoms_disj[xrows * found];
                                for (int i = 0; i < nconds * found; i++) {
                                    copytmdisj[i] = p_tmdisj[i];
                                }
                                for (int i = 0; i < 3 * found; i++) {
                                    copyticpr_disj[i] = p_ticpr_disj[i];
                                }
                                for (int i = 0; i < xrows * found; i++) {
                                    copytcoms_disj[i] = p_tcoms_disj[i];
                                }
                                for (int i = 0; i < p_depth[0] * found; i++) {
                                    tindx_disj[i] = p_indx_disj[i];
                                }
                                for (int i = 0; i < found; i++) {
                                    tck_disj[i] = p_ck_disj[i];
                                }
                                estim2 *= 2;
                                SET_VECTOR_ELT(usage,  9, tmdisj     = allocVector(INTSXP, nconds * estim2));
                                p_tmdisj = INTEGER(tmdisj);
                                SET_VECTOR_ELT(usage, 11, ticpr_disj = allocVector(REALSXP, 3 * estim2));
                                p_ticpr_disj = REAL(ticpr_disj);
                                SET_VECTOR_ELT(usage, 13, tcoms_disj = allocMatrix(REALSXP, xrows, estim2));
                                p_tcoms_disj = REAL(tcoms_disj);
                                SET_VECTOR_ELT(usage, 15, indx_disj  = allocVector(REALSXP, p_depth[0] * estim2));
                                p_indx_disj = INTEGER(indx_disj);
                                SET_VECTOR_ELT(usage, 17, ck_disj    = allocVector(INTSXP, estim2));
                                p_ck_disj = INTEGER(ck_disj);
                                for (int i = 0; i < nconds * found; i++) {
                                    p_tmdisj[i] = copytmdisj[i];
                                }
                                for (int i = 0; i < 3 * found; i++) {
                                    p_ticpr_disj[i] = copyticpr_disj[i];
                                }
                                for (int i = 0; i < xrows * found; i++) {
                                    p_tcoms_disj[i] = copytcoms_disj[i];
                                }
                                for (int i = 0; i < p_depth[0] * found; i++) {
                                    p_indx_disj[i] = tindx_disj[i];
                                }
                                for (int i = 0; i < found; i++) {
                                    p_ck_disj[i] = tck_disj[i];
                                }
                            }
                        }
                    }
                } 
            } 
        }
        foundk1 = found1;
        foundk2 = found;
        k++;
    }
    SEXP icpr_conj, icpr_disj, mconj, mdisj, coms_conj, coms_disj;
    SEXP result = PROTECT(allocVector(VECSXP, 6));
    SET_VECTOR_ELT(result, 0, icpr_conj = allocMatrix(REALSXP, found1, 3)); 
    SET_VECTOR_ELT(result, 1, icpr_disj = allocMatrix(REALSXP, found, 3)); 
    SET_VECTOR_ELT(result, 2, mconj = allocMatrix(INTSXP, found1, nconds)); 
    SET_VECTOR_ELT(result, 3, mdisj = allocMatrix(INTSXP, found, nconds)); 
    SET_VECTOR_ELT(result, 4, coms_conj = allocMatrix(REALSXP, xrows, found1)); 
    SET_VECTOR_ELT(result, 5, coms_disj = allocMatrix(REALSXP, xrows, found)); 
    double *p_icpr_conj = REAL(icpr_conj);
    double *p_icpr_disj = REAL(icpr_disj);
    int *p_mconj = INTEGER(mconj);
    int *p_mdisj = INTEGER(mdisj);
    double *p_coms_conj = REAL(coms_conj);
    double *p_coms_disj = REAL(coms_disj);
    for (int r = 0; r < found1; r++) { 
        for (int c = 0; c < 3; c++) {
            p_icpr_conj[c * found1 + r] = p_ticpr_conj[r * 3 + c];
        }
    }
    for (int r = 0; r < found1; r++) { 
        for (int c = 0; c < nconds; c++) {
            p_mconj[c * found1 + r] = p_tmconj[r * nconds + c];
        }
    }
    for (int r = 0; r < found; r++) { 
        for (int c = 0; c < 3; c++) {
            p_icpr_disj[c * found + r] = p_ticpr_disj[r * 3 + c];
        }
    }
    for (int r = 0; r < found; r++) { 
        for (int c = 0; c < nconds; c++) {
            p_mdisj[c * found + r] = p_tmdisj[r * nconds + c];
        }
    }
    for (int i = 0; i < xrows * found1; i++) {
        p_coms_conj[i] = p_tcoms_conj[i];
    }
    for (int i = 0; i < xrows * found; i++) {
        p_coms_disj[i] = p_tcoms_disj[i];
    }
    UNPROTECT(2);
    return(result);
}
