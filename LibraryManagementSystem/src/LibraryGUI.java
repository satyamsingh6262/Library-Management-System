import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

public class LibraryGUI extends JFrame {
    private LibraryManager manager = new LibraryManager();

    public LibraryGUI() {
        setTitle("Library Management System");
        setSize(600, 400);
        setDefaultCloseOperation(EXIT_ON_CLOSE);
        setLayout(new BorderLayout());

        JButton addBookBtn = new JButton("Add Book");
        addBookBtn.addActionListener(e -> {
            String title = JOptionPane.showInputDialog("Enter Title:");
            String author = JOptionPane.showInputDialog("Enter Author:");
            manager.addBook(title, author);
            JOptionPane.showMessageDialog(null, "Book added.");
        });

        JButton viewBooksBtn = new JButton("View Books");
        viewBooksBtn.addActionListener(e -> {
            JTextArea textArea = new JTextArea();
            manager.getAllBooks().forEach(book -> 
                textArea.append(book.getTitle() + " by " + book.getAuthor() + "\n")
            );
            JOptionPane.showMessageDialog(null, new JScrollPane(textArea), "Book List", JOptionPane.INFORMATION_MESSAGE);
        });

        JPanel panel = new JPanel();
        panel.add(addBookBtn);
        panel.add(viewBooksBtn);

        add(panel, BorderLayout.CENTER);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> new LibraryGUI().setVisible(true));
    }
}