<?php
session_start();

$receiving_email_address = 'contact@example.com';

if (file_exists($php_email_form = '../assets/vendor/php-email-form/php-email-form.php')) {
  include($php_email_form);
} else {
  die('Unable to load the "PHP Email Form" Library!');
}

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
  die("Forbidden request");
}

$name    = htmlspecialchars(trim($_POST['name'] ?? ''), ENT_QUOTES, 'UTF-8');
$phone   = preg_replace('/[^0-9+]/', '', $_POST['phone'] ?? '');
$subject = htmlspecialchars(trim($_POST['subject'] ?? ''), ENT_QUOTES, 'UTF-8');
$message = htmlspecialchars(trim($_POST['message'] ?? ''), ENT_QUOTES, 'UTF-8');

if (!empty($_POST['website'])) {
  die("Spam detected");
}

if (strlen($name) < 3) {
  die("Invalid name");
}

if (strlen($message) < 5) {
  die("Message too short");
}

$contact = new PHP_Email_Form;
$contact->ajax = true;

$contact->to = $receiving_email_address;

$contact->from_name = $name;
$contact->from_email = "no-reply@yourdomain.com";
$contact->subject = $subject;

$name = str_replace(array("\r", "\n"), '', $name);
$subject = str_replace(array("\r", "\n"), '', $subject);

$contact->add_message($name, 'Name');
$contact->add_message($phone, 'Phone');
$contact->add_message($subject, 'Car Model');
$contact->add_message($message, 'Message', 10);

echo $contact->send();
?>