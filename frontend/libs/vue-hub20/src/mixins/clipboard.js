export default {
    CopyToClipboardMixin: {
        props: {
            valueToCopy: {
                type: [Number, String, Object],
                default: null
            },
            toolTip: {
                type: String,
                default: 'click to copy'
            }
        },
        methods: {
            copyToClipboard: function() {
                if (!navigator.clipboard) {
                    return
                }

                let valueType = typeof(this.valueToCopy)
                let value

                switch (valueType) {
                case "number":
                case "object":
                    value = String(this.valueToCopy)
                    break
                default:
                    value = this.valueToCopy
                }

                if (value) {
                    navigator.clipboard.writeText(value);
                }
            }
        }
    }
}
