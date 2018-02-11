# Outback Power MATE3

## Introduction
[Outback Power](www.outbackpower.com)is a manufacturer of Solar power systems (among other things). I selected their products because they offer some great integration and data collection.

The software in this repository can be used to extract data from the MATE3 control head.

Note that this code only outputs to text, but can obviously easily be converted over to output in other formats.

##MODBUS? SunSpec?
Modbus is a pretty old industrial automation protocol. Implementations usually have some funky mapping to map current data formats to MODBUS. The MATE3 uses a renewable energy spec called SunSpec. It defines most conversions etc, same differences in the Outback implementation

## Testing
I have only tested this code with my own equipment:
* [MATE3](http://www.outbackpower.com/outback-products/manage-the-system/mate3-system-display-and-controller/item/mate3s?category_id=545), System display and controller (note, not tested with newer MATE3s)
* [HUB4](http://www.outbackpower.com/outback-products/manage-the-system/hub-communication-manager), System Communications Manager
* [FXR3048A](http://www.outbackpower.com/outback-products/make-the-power/fxr-series-inverter-chargers/item/fxr-renewable-series-120v-a-models?category_id=530), Inverter
* [FLEXMAX80](http://www.outbackpower.com/outback-products/make-the-power/flexmax-series-charge-controllers/item/flexmax-6080?category_id=531), Charge controller
* [FLEXnet-DC](http://www.outbackpower.com/outback-products/manage-the-system/flexnet-dc), Battery monitor (provides power balance)

If you have other equipment, please let me know and I can add support pretty easily.

## Dependencies
Pymodbus

## Issues
* Inverter AC USE variable seems to not read correctly (I suspect this is a firmware issue)
