odoo.define('pos_button_in_header.CustomTopButtonFile', function (require) {
    'use strict';

    const PosComponent = require("point_of_sale.PosComponent");
    const Registries = require("point_of_sale.Registries");

    class CustomTopButtonClss extends PosComponent {
        onClick(){
            this.showPopup("ErrorPopup",{
                title: this.env._t("Custom Top Button Clicked"),
                body: this.env._t("Welcome to OWL, From top Button"),
            });
        }
    }
    CustomTopButtonClss.template = "CustomTopButtonTemp";
    Registries.Component.add(CustomTopButtonClss);

    });