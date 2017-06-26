# include <R.h>
# include <Rinternals.h>
# include <Rmath.h>
# include <R_ext/Rdynload.h>
SEXP allSol(SEXP k, SEXP mtrx) {
    SEXP root, temp1, temp2;
    int *p_k, *p_mtrx, *p_output, lmbasej, x, y, mtrxrows, mtrxcols, base2count, totalcount, flag;
    int *p_work, i, j, *p_temp1, *p_temp2, lungime, lengthtemp1, *p_rn; 
    PROTECT(root = Rf_allocVector(VECSXP, 7));
    SET_VECTOR_ELT(root, 0, k = coerceVector(k, INTSXP));
    SET_VECTOR_ELT(root, 1, mtrx = coerceVector(mtrx, INTSXP));
    p_k = INTEGER(k);
    p_mtrx = INTEGER(mtrx);
    mtrxrows = nrows(mtrx);
    mtrxcols = ncols(mtrx);
    int colsums[mtrxcols];
    long long int power[mtrxrows];
    power[mtrxrows - 1] = 1;
    for (j = 1; j < mtrxrows; j++) {
        power[mtrxrows - j - 1] = R_pow_di(2, j);
    }
    long long int totalrows = power[0]*2;
    SEXP work = SET_VECTOR_ELT(root, 2, allocVector(INTSXP, totalrows));
    p_work = INTEGER(work);
    for (i = 0; i < totalrows; i++) {
        p_work[i] = 0;
    }
    totalcount = 0;
    int base2row[mtrxrows];
    for (i = 1; i < totalrows; i++) {
        if (p_work[i] >= 0) {
            base2count = 0;
            for (j = 0; j < mtrxcols; j++) {
                colsums[j] = 0;
            }
            for (j = 0; j < mtrxrows; j++) {
                base2row[mtrxrows - j - 1] = div(div(i, power[mtrxrows - j - 1]).quot, 2).rem;
            }
            for (j = 0; j < mtrxrows; j++) {
                base2count += base2row[j];
                if (base2row[j] == 1) {
                    for (x = 0; x < mtrxcols; x++) {
                        colsums[x] += p_mtrx[j + mtrxrows * x];
                    }
                }
            }
            flag = 1;
            for (x = 0; x < mtrxcols; x++) {
                if (colsums[x] == 0) {
                    flag = 0;
                }
            }
            if (base2count < p_k[0]) {
                flag = 0;
            }
            if (flag == 0) {
                p_work[i] = 0;
            }
            else {
                p_work[i] = 1;
                totalcount += 1;
                lungime = 1;
                SET_VECTOR_ELT(root, 3, temp1 = allocVector(INTSXP, lungime));
                p_temp1 = INTEGER(temp1);
                p_temp1[0] = i;
                flag = 0; 
                for (j = 0; j < mtrxrows; j++) {
                    lmbasej = mtrxrows - j - 1;
                    if (base2row[lmbasej] == 0) {
                        flag = 1; 
                        lungime = lungime * 2; 
                        SET_VECTOR_ELT(root, 4, temp2 = allocVector(INTSXP, lungime));
                        p_temp2 = INTEGER(temp2);
                        lengthtemp1 = length(temp1);
                        for (x = 0; x < lengthtemp1; x++) {
                            p_temp2[x] = p_temp1[x];
                            p_temp2[x + lengthtemp1] = p_temp1[x] + power[lmbasej];
                        }
                        if (j < mtrxrows) {
                            SET_VECTOR_ELT(root, 3, temp1 = allocVector(INTSXP, lungime));
                            p_temp1 = INTEGER(temp1);
                            for (x = 0; x < lungime; x++) {
                                p_temp1[x] = p_temp2[x];
                            }
                        }
                    }
                }
                if (flag == 1) {
                    for (x = 1; x < length(temp2); x++) {
                        p_work[p_temp2[x]] = -1;
                    }
                }
            }
        }
        else {
            p_work[i] = 0;
        }
    }
    int b2rs[totalcount];
    SEXP rn = SET_VECTOR_ELT(root, 5, allocVector(INTSXP, totalcount));
    SEXP output = SET_VECTOR_ELT(root, 6, allocMatrix(INTSXP, mtrxrows, totalcount));
    p_rn = INTEGER(rn);
    p_output = INTEGER(output);
    if (totalcount > 1) { 
        x = 0;
        for (i = 0; i < totalrows; i++) {
            if (p_work[i] == 1) {
                p_rn[x] = i;
                b2rs[x] = 0;
                for (j = 0; j < mtrxrows; j++) {
                    b2rs[x] += div(div(i, power[mtrxrows - j - 1]).quot, 2).rem; 
                }
                x += 1;
            }
        }
        for (i = 0; i < totalcount - 1; i++) {
            x = i;
            for (j = i + 1; j < totalcount; j++) {
                if (b2rs[i] > b2rs[j]) {
                    x = j;
                }
            }
            if (x != i) {
                y = b2rs[i];
                b2rs[i] = b2rs[x];
                b2rs[x] = y;
                y = p_rn[i];
                p_rn[i] = p_rn[x];
                p_rn[x] = y;
            }
        }
        for (i = 0; i < totalcount - 1; i++) {
            x = i;
            for (j = i + 1; j < totalcount; j++) {
                if (b2rs[i] == b2rs[j] && p_rn[i] > p_rn[j]) {
                    x = j;
                }
            }
            if (x != i) {
                y = p_rn[i];
                p_rn[i] = p_rn[x];
                p_rn[x] = y;
            }
        }
    }
    else {
        for (i = 0; i < totalrows; i++) {
            if (p_work[i] == 1) {
                p_rn[0] = i; 
            }
        }
    }
    x = 0;
    for (i = 0; i < totalcount; i++) {
        for (j = 0; j < mtrxrows; j++) {
            p_output[x] = div(div(p_rn[i], power[j]).quot, 2).rem; 
            if (p_output[x] == 1) {
                p_output[x] = j + 1;
            }
            x += 1;
        }
    }
    UNPROTECT(1);
    return(output);
}
