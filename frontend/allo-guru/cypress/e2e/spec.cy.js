describe('Status Page Tests', () => {
  beforeEach(() => {
    cy.visit('http://localhost:3000'); // Replace with your app's URL
  });

  it('Displays the service status message', () => {
    cy.contains('.serviceMessage', '✅ Allo is online! Last updated at 2023-12-09 02:44:53');
  });

  it('Allows user to enter an email', () => {
    cy.get('.inputField').type('test@example.com');
  });

  it('Shows error for invalid email', () => {
    cy.get('.inputField').clear().type('test@example.com');
    cy.get('.subscribeButton').click();
    cy.contains('.formElement', 'The domain name example.com does not accept email.');
  });

  it('Shows success message after subscribing', () => {
    cy.intercept('POST', 'https://www.allo.guru/api/subscribe', {
      statusCode: 200,
      body: { message: 'Successfully subscribed to notifications' },
    }).as('subscribeRequest');

    cy.get('.inputField').clear().type('zdvylsydcskqngmpba@cwmxc.com');
    cy.get('.subscribeButton').click();
    cy.wait('@subscribeRequest');
    cy.contains('Successfully subscribed to notifications');
  });

});
