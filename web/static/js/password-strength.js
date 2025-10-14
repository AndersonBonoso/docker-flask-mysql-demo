// Calcula força com base em tamanho e classes de caracteres.
// Atualiza a barra e o label quando existir #password, #strengthBar, #strengthLabel.

(function () {
    function scorePassword(pw) {
        if (!pw) return 0;
        let s = 0;
        const len = pw.length;

        // comprimento
        s += Math.min(10, len) * 5; // até 50

        // diversidade
        const hasLower = /[a-z]/.test(pw);
        const hasUpper = /[A-Z]/.test(pw);
        const hasDigit = /\d/.test(pw);
        const hasSpec  = /[^\w\s]/.test(pw);
        const groups = [hasLower, hasUpper, hasDigit, hasSpec].filter(Boolean).length;
        s += (groups - 1) * 15; // +0..45

        // bônus leve por não repetição óbvia
        if (!/(.)\1{2,}/.test(pw)) s += 5;

        return Math.max(0, Math.min(100, s));
    }

    function labelFor(score) {
        if (score < 20) return ["muito fraca", "bg-danger"];
        if (score < 40) return ["fraca", "bg-danger"];
        if (score < 60) return ["ok", "bg-warning"];
        if (score < 80) return ["forte", "bg-success"];
        return ["muito forte", "bg-success"];
    }

    function setup() {
        const input = document.getElementById("password");
        const bar = document.getElementById("strengthBar");
        const label = document.getElementById("strengthLabel");
        if (!input || !bar || !label) return;

        const update = () => {
        const v = input.value || "";
        const score = scorePassword(v);
        const [txt, cls] = labelFor(score);
        bar.style.width = score + "%";
        bar.className = "progress-bar " + cls;
        label.textContent = "Força: " + txt;
        };

        input.addEventListener("input", update);
        update();
    }

    document.addEventListener("DOMContentLoaded", setup);
})();
