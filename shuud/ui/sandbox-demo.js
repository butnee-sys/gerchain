// SHUUD investor/official demo helper layer.
// Kept separate from the main UI so the demo can be reused by the web and mobile shells.
window.SHUUD_DEMO = {
  targetSeconds: 120,
  headline: '2 минутын дотор замаа чөлөөл',
  stages: [
    ['INCIDENT_CREATED', 'Тохиолдол мэдээлсэн'],
    ['EVIDENCE_LOCKED', 'Баримт баталгаажсан'],
    ['SHIID_APPROVED', 'SHIID шийдвэр'],
    ['ESCROW_LOCKED', 'Төлбөрийн эх үүсвэр баталгаажсан'],
    ['CLEARED', 'Зам чөлөөлсөн'],
    ['PAYMENT_RELEASED', 'Төлбөр гарсан'],
  ],
  isWithinTarget(seconds) {
    return Number(seconds) <= this.targetSeconds;
  },
};
