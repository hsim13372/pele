#ifndef _PELE_PRESSURE_TENSOR_H
#define _PELE_PRESSURE_TENSOR_H

namespace pele {

double pressure_tensor(std::shared_prt<pele::BasePotential> pot,
                       const pele::Array<double>& x,
                       pele::Array<double>& ptensor,
                       const double volume);
    
} // namespace pele

#endif // #ifndef _PELE_PRESSURE_TENSOR_H
